from django.db import transaction
from django.db.models import F, QuerySet

from apps.notifications.models import Notification
from apps.notifications.utils import reset_cache_noti, set_cache_noti_for_dm_all
from apps.users.models import User


def get_notification_list(user: User) -> QuerySet[Notification]:
    queryset = Notification.objects.filter(receiver=user).select_related("sender")
    return queryset


def read_all_notifications(user: User) -> None:
    with transaction.atomic():
        Notification.objects.filter(receiver=user, is_read=False).update(is_read=True)
        User.objects.filter(id=user.id).update(unread_noti_count=0)

    reset_cache_noti(user)


def delete_all_notifications(user: User) -> None:
    with transaction.atomic():
        Notification.objects.filter(receiver=user).delete()
        User.objects.filter(id=user.id).update(unread_noti_count=0)

    reset_cache_noti(user)


def read_all_about_conversation_dm(user: User, conversation_id: str) -> None:
    with transaction.atomic():
        count = Notification.objects.filter(
            receiver=user, target_id=conversation_id, is_read=False
        ).update(is_read=True)
        if count:
            User.objects.filter(id=user.id).update(
                unread_noti_count=F("unread_noti_count") - count
            )

    set_cache_noti_for_dm_all(user, count)
