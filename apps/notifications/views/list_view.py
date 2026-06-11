from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_notification_list(request.user.id)
        return paginate(queryset, request, NotificationListSerializer)
