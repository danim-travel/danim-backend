from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.schemas.me_schema import user_me_schema, user_update_schema
from apps.users.serializers.me_serializer import (
    UserDeleteRequestSerializer,
    UserInfoResponseSerializer,
    UserUpdateRequestSerializer,
    UserUpdateResponseSerializer,
)
from apps.users.services.me_service import UserDeleteService, UserUpdateService


class UserMeView(APIView):

    permission_classes = [IsAuthenticated]
    update_service = UserUpdateService()
    delete_service = UserDeleteService()

    @user_me_schema
    def get(self, request: Request) -> Response:

        serializer = UserInfoResponseSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @user_update_schema
    def patch(self, request: Request) -> Response:
        serializer = UserUpdateRequestSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        update_user = self.update_service.user_update(
            user=cast(User, request.user),
            data=serializer.validated_data,
        )
        return Response(
            UserUpdateResponseSerializer(update_user).data, status=status.HTTP_200_OK
        )

    def delete(self, request: Request) -> Response:
        serializer = UserDeleteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.delete_service.user_delete(
            user=cast(User, request.user),
            password=serializer.validated_data.get("password"),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
