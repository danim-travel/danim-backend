from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications.schemas import (
    notification_delete_schema,
    notification_read_schema,
)
from apps.notifications.services import delete_notification, read_notification


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    @notification_read_schema
    def patch(self, request, notification_id):
        result = read_notification(notification_id, request.user)
        return Response(result, status=status.HTTP_200_OK)

    @notification_delete_schema
    def delete(self, request, notification_id):
        result = delete_notification(notification_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
