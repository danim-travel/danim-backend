from apps.notifications.models import Notification
from apps.notifications.utils import reset_cache_noti


def get_notification_list(user):
    queryset = Notification.objects.filter(receiver=user).select_related("sender")
    return queryset


def read_all_notifications(user):
    Notification.objects.filter(receiver=user, is_read=False).update(is_read=True)

    reset_cache_noti(user)


def delete_all_notifications(user):
    Notification.objects.filter(receiver=user).delete()

    reset_cache_noti(user)
