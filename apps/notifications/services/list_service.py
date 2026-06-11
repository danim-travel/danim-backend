from apps.notifications.models import Notification


def get_notification_list(user):
    queryset = Notification.objects.filter(receiver=user).select_related("sender")
    return queryset
