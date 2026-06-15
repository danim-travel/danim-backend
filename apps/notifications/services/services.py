from django.core.cache import cache

from apps.core.exceptions.exception import NotFoundException
from apps.notifications.models import Notification


def read_notification(notification_id, user):
    notification = Notification.objects.filter(
        id=notification_id, receiver=user, is_read=False
    ).update(is_read=True)
    if not notification:
        raise NotFoundException("해당 알림을 찾지 못했습니다.")

    result = {"notification_id": notification_id, "is_read": True}

    try:
        cache.decr(f"user_{user.id}_unread_count")
    except ValueError:
        cache.set(
            f"user_{user.id}_unread_count",
            Notification.objects.filter(receiver=user, is_read=False).count(),
            timeout=None,
        )

    return result
