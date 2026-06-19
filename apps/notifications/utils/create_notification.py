from typing import Literal

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.cache import cache

from apps.notifications.models.model import Notification, NotificationType, TargetChoices
from apps.users.models import User

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
    receiver_id,
    sender: User,
    noti_type: Literal["post_like", "comment", "comment_like", "follow", "dm"],
    target_id: str,
):
    if receiver_id == sender.id:
        return
    target_type, msg_base = NOTIFICATION_MAP[noti_type]
    msg = msg_base.format(sender.nickname)
    create_noti(sender, receiver_id, noti_type, target_id, target_type, msg)


def create_noti(sender, receiver_id, noti_type, target_id, target_type, msg):
    try:
        Notification.objects.create(
            sender=sender,
            receiver_id=receiver_id,
            notification_type=noti_type,
            target_id=target_id,
            target_type=target_type,
            message=msg,
        )
        try:
            cache.incr(f"user_{receiver_id}_unread_count")
        except ValueError:
            cache.set(
                f"user_{receiver_id}_unread_count",
                Notification.objects.filter(
                    receiver_id=receiver_id,
                    is_read=False,
                ).count(),
                timeout=None,
            )
        push_channel_noti(receiver_id)

    except Exception:
        pass


def push_channel_noti(receiver_id: str):
    """
    WebSocket을 통해 유저의 읽지 않은 알림 개수를 실시간으로 전송하는 함수
      receiver = 알림을 수신할 유저
    """
    channel_layer = get_channel_layer()
    unread_count = cache.get(f"user_{receiver_id}_unread_count")
    async_to_sync(channel_layer.group_send)(
        f"user_{receiver_id}",
        {"type": "send_unread_count", "count": unread_count},
    )


def set_cache_noti_for_rd(receiver: User):
    """개별 알림 읽음 처리 및 개별 알림 삭제 처리 redis cache 갱신 함수"""
    try:
        cache.decr(f"user_{receiver.id}_unread_count")
    except ValueError:
        cache.set(
            f"user_{receiver.id}_unread_count",
            Notification.objects.filter(receiver=receiver, is_read=False).count(),
            timeout=None,
        )
    try:
        push_channel_noti(receiver.id)
    except Exception:
        pass


def reset_cache_noti(receiver: User):
    """전체 읽음 처리 및 전체 삭제 처리 redis 초기화 함수"""
    cache.set(f"user_{receiver.id}_unread_count", 0, timeout=None)
    try:
        push_channel_noti(receiver.id)
    except Exception:
        pass
