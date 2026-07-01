from apps.notifications.models import Notification
from apps.notifications.utils import reset_cache_noti, set_cache_noti_for_dm_all


def get_notification_list(user):
    queryset = Notification.objects.filter(receiver=user).select_related("sender")
    return queryset


def read_all_notifications(user):
    Notification.objects.filter(receiver=user, is_read=False).update(is_read=True)

    reset_cache_noti(user)


def delete_all_notifications(user):
    Notification.objects.filter(receiver=user).delete()

    reset_cache_noti(user)


def read_all_about_conversation_dm(user, conversation_id):
    count = Notification.objects.filter(
        receiver=user, target_id=conversation_id, is_read=False
    ).update(is_read=True)

    set_cache_noti_for_dm_all(user, count)
