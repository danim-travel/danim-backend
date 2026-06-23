from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.notifications.schemas import (
    notification_delete_all_schema,
    notification_list_schema,
    notification_read_all_schema,
)
from apps.notifications.serializers import NotificationListSerializer
from apps.notifications.services import (
    delete_all_notifications,
    get_notification_list,
    read_all_notifications,
)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @notification_list_schema
    def get(self, request):
        queryset = get_notification_list(request.user)
        return paginate(queryset, request, NotificationListSerializer)

    @notification_read_all_schema
    def patch(self, request):
        read_all_notifications(request.user)
        return Response(
            {"message": "모든 알림이 읽음 처리 되었습니다."}, status=status.HTTP_200_OK
        )

    @notification_delete_all_schema
    def delete(self, request):
        delete_all_notifications(request.user)
        return Response(
            {"message": "모든 알림이 삭제 처리 되었습니다."}, status=status.HTTP_200_OK
        )
