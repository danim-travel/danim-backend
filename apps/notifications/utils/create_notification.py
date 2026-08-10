import logging
from typing import Literal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Greatest

from apps.notifications.models.model import Notification, NotificationType, TargetChoices
from apps.users.models import User

logger = logging.getLogger(__name__)

CACHE_UNREAD_TIMEOUT = 60 * 60 * 24  # 24시간

# 반드시 kombu visibility_timeout(기본 3600초)보다 작아야 한다. 선점 후 생성 전에 워커가
# 죽으면(mem_limit OOM-kill을 상정한 구성) 보상(cache.delete)이 돌지 못하고 태스크 재배달로만
# 복구되는데, TTL이 그보다 길면 재배달된 태스크가 살아있는 키에 막혀 알림이 유실된다.
NOTI_DEDUP_TTL = 30

# dedup 키는 target_id로 행위 대상을 식별하는데, target_id는 "알림 클릭 시 이동할 위치"
# (TargetChoices)를 담는 필드라 댓글 계열은 전부 게시글 ID가 들어간다. 즉 comment/
# comment_like/dm은 서로 다른 댓글·메시지가 같은 키로 뭉개져 정상 알림까지 막힌다.
# target_id가 행위 대상과 1:1로 대응하는 두 종류에만 적용한다.
DEDUP_NOTI_TYPES = frozenset({NotificationType.POST_LIKE, NotificationType.FOLLOW})

NOTIFICATION_MAP: dict[str, tuple[str, str]] = {
    NotificationType.COMMENT: (
        TargetChoices.POST,
        "{}님이 회원님의 게시글에 댓글을 작성했습니다.",
    ),
    NotificationType.COMMENT_LIKE: (
        TargetChoices.POST,
        "{}님이 회원님의 댓글에 좋아요를 눌렀습니다.",
    ),
    NotificationType.POST_LIKE: (
        TargetChoices.POST,
        "{}님이 회원님의 게시글에 좋아요를 눌렀습니다.",
    ),
    NotificationType.FOLLOW: (TargetChoices.USER, "{}님이 회원님을 팔로우 했습니다."),
    NotificationType.DM: (TargetChoices.DM, "{}님이 회원님께 메세지를 보냈습니다."),
}


def create_notification(
    receiver_id: str,
    sender: User,
    noti_type: Literal["post_like", "comment", "comment_like", "follow", "dm"],
    target_id: str,
) -> None:
    if receiver_id == sender.id:
        return
    dedup_key = _build_dedup_key(receiver_id, sender.id, noti_type, target_id)
    if dedup_key is not None and not _reserve_dedup_key(dedup_key):
        return
    try:
        # 차단 관계면 알림을 만들지 않는다 — 시그널 5곳을 개별 수정하는 대신
        # 모든 알림이 통과하는 이 중앙 게이트 한 곳에서 막는다.
        from apps.blocks.services import is_blocked_between

        if is_blocked_between(receiver_id, sender.id):
            return
        target_type, msg_base = NOTIFICATION_MAP[noti_type]
        msg = msg_base.format(sender.nickname)
        create_noti(sender, receiver_id, noti_type, target_id, target_type, msg)
    except Exception:
        # 선점만 해두고 생성에 실패하면 키가 TTL 동안 남아, celery 재시도
        # (countdown 1·2·4초, 전부 TTL 안)가 중복으로 오인돼 조용히 no-op이 된다.
        # 태스크는 성공으로 기록되어 알림이 영구 유실되므로 선점을 되돌린다.
        # create_noti의 예외는 transaction.atomic() 안에서 발생해 커밋된 것이 없으므로
        # 재시도가 중복 알림을 만들지 않는다.
        if dedup_key is not None:
            cache.delete(dedup_key)
        raise


SYSTEM_SENDER_NAME = "다님 고객센터"

# 발신 주체가 사람이 아니라 서비스인 알림. 목록 serializer는 sender=None을 "탈퇴한 유저"로
# 표시하므로(원래 SET_NULL 전용 분기), 이 집합에 속한 종류는 그 분기 대신
# SYSTEM_SENDER_NAME을 쓴다. 새 시스템 알림을 추가하면 여기에도 넣어야 표시가 맞는다.
SYSTEM_NOTI_TYPES = frozenset({NotificationType.INQUIRY_ANSWERED})


def create_system_notification(
    receiver_id: str, noti_type: str, target_id: str, target_type: str, msg: str
) -> None:
    """발신 주체가 서비스인 알림(문의 답변 등)을 만든다.

    사용자 간 경로(create_notification)를 쓰지 않는 이유:
      - 차단 게이트: 사용자가 운영자 계정을 차단해 두면 본인이 먼저 요청한 답변
        알림이 조용히 사라진다. 사회적 관계로 막을 대상이 아니다.
      - NOTIFICATION_MAP: 모든 문구가 sender 닉네임을 포맷에 넣는데, 발신 주체가
        특정 운영자가 아니고 담당자 신원이 사용자에게 노출돼서도 안 된다.
      - 자기 알림 차단(receiver == sender): sender가 없어 성립하지 않는다.
    dedup도 걸지 않는다 — 시스템 알림은 사용자 행위 반복으로 폭증하는 축이 아니다.
    """
    create_noti(None, receiver_id, noti_type, target_id, target_type, msg)


def _build_dedup_key(
    receiver_id: str, sender_id: str, noti_type: str, target_id: str
) -> str | None:
    """dedup 대상이면 키를, 아니면 None을 반환한다.

    조건: DEDUP_NOTI_TYPES에 속한 종류에만 키를 만든다. target_id는 원래 "알림 클릭 시
        이동할 위치"를 담는 필드라, 댓글 계열은 서로 다른 댓글이 같은 게시글 ID로
        뭉개져 정상 알림까지 막히기 때문이다.
    """
    if noti_type not in DEDUP_NOTI_TYPES:
        return None
    return f"noti:dedup:{receiver_id}:{sender_id}:{noti_type}:{target_id}"


def _reserve_dedup_key(dedup_key: str) -> bool:
    """중복이 아니면 키를 선점하고 True를 반환한다.

    기능: 좋아요/팔로우 취소 후 재실행을 반복하면 post_save(created=True)가 매번
        발화해 알림이 무제한 생성된다. cache.add는 키가 없을 때만 저장하는 원자적
        연산이라, 동시 요청 중 하나만 통과한다.
    예외: Redis 장애 시 cache.add가 None을 반환하면(캐시 default 별칭은
        IGNORE_EXCEPTIONS=True) 알림을 통과시킨다 — 알림 유실보다 중복이 낫다(fail-open).
    """
    added = cache.add(dedup_key, 1, timeout=NOTI_DEDUP_TTL)
    if added is None:
        return True
    return added


def create_noti(
    sender: User | None,
    receiver_id: str,
    noti_type: str,
    target_id: str,
    target_type: str,
    msg: str,
) -> None:
    """알림 행을 만들고 미읽음 카운트·캐시·웹소켓 푸시를 갱신한다.

    계약: **커밋 이후 구간(캐시 증감, 웹소켓 푸시)의 예외를 밖으로 내보내지 않는다.**
        create_notification의 보상 로직이 "예외가 나왔다 = 커밋된 것이 없다"를 전제로
        dedup 키를 해제하기 때문이다. 아래 try/except를 걷어내 푸시 실패를 드러내면,
        이미 생성된 알림에 대해 키가 풀려 재시도가 중복 알림을 만든다.

    sender가 None이면 시스템 발신 알림이다(문의 답변 등). Notification.sender는
    이미 null 허용이라 저장 자체는 원래 가능했고, 여기서는 타입만 실제와 맞춘다.
    사용자 간 알림은 create_notification을 거치고, 이 함수를 직접 부르는 쪽은
    차단 게이트·dedup·닉네임 포맷이 필요 없는 시스템 알림 경로다.
    """
    try:
        with transaction.atomic():
            Notification.objects.create(
                sender=sender,
                receiver_id=receiver_id,
                notification_type=noti_type,
                target_id=target_id,
                target_type=target_type,
                message=msg,
            )
            User.objects.filter(id=receiver_id).update(
                unread_noti_count=Greatest(F("unread_noti_count") + 1, Value(0))
            )
    except Exception as e:
        logger.error(
            f"[알림 생성 실패] receiver_id={receiver_id}, noti_type={noti_type}, error={e}",
            exc_info=True,
        )
        raise
    try:
        cache_count = cache.incr(f"user_{receiver_id}_unread_count")
        if cache_count is None:
            logger.warning(
                f"[알림 캐시 설정 실패] Redis 장애 가능성 receiver_id={receiver_id}"
            )
            _sync_cache_from_db_by_id(receiver_id)
    except Exception:
        try:
            _sync_cache_from_db_by_id(receiver_id)
        except Exception as e:
            logger.warning(f"[캐시 DB 동기화 실패] receiver_id={receiver_id}, error={e}")
    try:
        push_channel_noti(receiver_id)
    except Exception as e:
        logger.warning(f"[알림 푸시 실패] receiver_id={receiver_id}, error={e}")


def _sync_cache_from_db_by_id(receiver_id: str) -> None:
    real_count = (
        User.objects.filter(id=receiver_id)
        .values_list("unread_noti_count", flat=True)
        .first()
        or 0
    )
    cache.set(
        f"user_{receiver_id}_unread_count", real_count, timeout=CACHE_UNREAD_TIMEOUT
    )


def _sync_cache_from_db(receiver: User) -> None:
    _sync_cache_from_db_by_id(str(receiver.id))


def push_channel_noti(receiver_id: str) -> None:
    """
    WebSocket을 통해 유저의 읽지 않은 알림 개수를 실시간으로 전송하는 함수
      receiver = 알림을 수신할 유저
    """
    channel_layer = get_channel_layer()
    unread_count = cache.get(f"user_{receiver_id}_unread_count")
    if unread_count is None:
        unread_count = (
            User.objects.filter(id=receiver_id)
            .values_list("unread_noti_count", flat=True)
            .first()
            or 0
        )
    async_to_sync(channel_layer.group_send)(
        f"user_{receiver_id}",
        {"type": "send_unread_count", "count": unread_count},
    )


def set_cache_noti_for_rd(receiver: User) -> None:
    """개별 알림 읽음 처리 및 개별 알림 삭제 처리 redis cache 갱신 함수"""
    try:
        cache_count = cache.decr(f"user_{receiver.id}_unread_count")
        if cache_count is None:
            logger.warning(
                f"[알림 캐시 설정 실패] Redis 장애 가능성 receiver_id={receiver.id}"
            )
            _sync_cache_from_db(receiver)
        elif cache_count < 0:
            raise ValueError
    except (ValueError, TypeError):
        _sync_cache_from_db(receiver)
    try:
        push_channel_noti(receiver.id)
    except Exception as e:
        logger.warning(f"[알림 푸시 실패] receiver_id={receiver.id}, error={e}")


def reset_cache_noti(receiver: User) -> None:
    """전체 읽음 처리 및 전체 삭제 처리 redis 초기화 함수"""
    cache.set(f"user_{receiver.id}_unread_count", 0, timeout=CACHE_UNREAD_TIMEOUT)
    try:
        push_channel_noti(receiver.id)
    except Exception as e:
        logger.warning(f"[알림 푸시 실패] receiver_id={receiver.id}, error={e}")


def set_cache_noti_for_dm_all(receiver: User, count: int) -> None:
    if not count:
        return
    try:
        cache_count = cache.decr(f"user_{receiver.id}_unread_count", count)
        if cache_count is None:
            logger.warning(
                f"[알림 캐시 설정 실패] Redis 장애 가능성 receiver_id={receiver.id}"
            )
            _sync_cache_from_db(receiver)
        elif cache_count < 0:
            raise ValueError
    except (ValueError, TypeError):
        _sync_cache_from_db(receiver)
    try:
        push_channel_noti(receiver.id)
    except Exception as e:
        logger.warning(f"[알림 푸시 실패] receiver_id={receiver.id}, error={e}")
