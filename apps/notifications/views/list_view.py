from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.notifications.serializers import NotificationListSerializer
from apps.notifications.services import get_notification_list


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_notification_list(request.user)
        return paginate(queryset, request, NotificationListSerializer)
