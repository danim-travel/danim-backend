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
    target_type, msg_base = NOTIFICATION_MAP[noti_type]
    msg = msg_base.format(sender.nickname)
    create_noti(sender, receiver_id, noti_type, target_id, target_type, msg)


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
        try:
            cache_count = cache.incr(f"user_{receiver_id}_unread_count")
            if cache_count is None:
                logger.warning(
                    f"[알림 캐시 설정 실패] Redis 장애 가능성 receiver_id={receiver_id}"
                )
                _sync_cache_from_db_by_id(receiver_id)
        except Exception:
            _sync_cache_from_db_by_id(receiver_id)
        try:
            push_channel_noti(receiver_id)
        except Exception as e:
            logger.warning(f"[알림 푸시 실패] receiver_id={receiver_id}, error={e}")

    except Exception as e:
        logger.error(
            f"[알림 생성 실패] receiver_id={receiver_id}, noti_type={noti_type}, error={e}",
            exc_info=True,
        )


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
    unread_count = cache.get(f"user_{receiver_id}_unread_count", 0)
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
