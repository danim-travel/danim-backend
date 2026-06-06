from typing import Any

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.serializers.user_update_delete_serializer import (
    UserUpdateRequestSerializer,
    UserUpdateResponseSerializer,
)
from apps.users.services.user_update_delete_service import UserUpdateService


class UserMeView(APIView):

    permission_classes = [IsAuthenticated]
    update_service = UserUpdateService()

    def patch(self, request: Request) -> Response:
        serializer = UserUpdateRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        update_user = self.update_service.user_update(
            user=request.user,
            data=serializer.validated_data,
        )
        return Response(
            UserUpdateResponseSerializer(update_user).data, status=status.HTTP_200_OK
        )
