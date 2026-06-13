from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        result = read_notification(notification_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
