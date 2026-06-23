from apps.core.exceptions.exception import NotFoundException
from apps.notifications.models import Notification
from apps.notifications.utils import set_cache_noti_for_rd


def read_notification(notification_id, user):
    notification = Notification.objects.filter(
        id=notification_id, receiver=user, is_read=False
    ).update(is_read=True)
    if not notification:
        raise NotFoundException("해당 알림을 찾지 못했습니다.")

    result = {"notification_id": notification_id, "is_read": True}

    set_cache_noti_for_rd(user)

    return result


def delete_notification(notification_id, user):
    is_unread = Notification.objects.filter(
        id=notification_id, receiver=user, is_read=False
    ).exists()

    deleted_count, _ = Notification.objects.filter(
        id=notification_id, receiver=user
    ).delete()
    if not deleted_count:
        raise NotFoundException("해당 알림을 찾지 못했습니다.")

    if is_unread:
        set_cache_noti_for_rd(user)

    return {"notification_id": notification_id}
