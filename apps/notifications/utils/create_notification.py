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
    if not _mark_not_duplicated(receiver_id, sender.id, noti_type, target_id):
        return
    # 차단 관계면 알림을 만들지 않는다 — 시그널 5곳을 개별 수정하는 대신
    # 모든 알림이 통과하는 이 중앙 게이트 한 곳에서 막는다.
    from apps.blocks.services import is_blocked_between

    if is_blocked_between(receiver_id, sender.id):
        return
    target_type, msg_base = NOTIFICATION_MAP[noti_type]
    msg = msg_base.format(sender.nickname)
    create_noti(sender, receiver_id, noti_type, target_id, target_type, msg)


def _mark_not_duplicated(
    receiver_id: str, sender_id: str, noti_type: str, target_id: str
) -> bool:
    """같은 알림이 짧은 시간에 반복 생성되는 것을 막는다.

    기능: 좋아요/팔로우 취소 후 재실행을 반복하면 post_save(created=True)가 매번
        발화해 알림이 무제한 생성된다. TTL 안에서 첫 호출만 True를 반환한다.
    조건: DEDUP_NOTI_TYPES에 속한 종류에만 적용한다. 그 외에는 항상 True.
    예외: Redis 장애 시 cache.add가 None을 반환하면(캐시 default 별칭은
        IGNORE_EXCEPTIONS=True) 알림을 통과시킨다 — 알림 유실보다 중복이 낫다(fail-open).
    """
    if noti_type not in DEDUP_NOTI_TYPES:
        return True
    dedup_key = f"noti:dedup:{receiver_id}:{sender_id}:{noti_type}:{target_id}"
    added = cache.add(dedup_key, 1, timeout=NOTI_DEDUP_TTL)
    if added is None:
        return True
    return added


def create_noti(
    sender: User,
    receiver_id: str,
    noti_type: str,
    target_id: str,
    target_type: str,
    msg: str,
) -> None:
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
