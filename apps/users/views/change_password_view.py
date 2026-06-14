from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.serializers.change_password_serializer import (
    ChangePasswordRequestSerializer,
)
from apps.users.services.change_password_service import ChangePasswordService


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    service = ChangePasswordService()

    def post(self, request: Request) -> Response:
        serializer = ChangePasswordRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.change_password(
            cast(User, request.user),
            serializer.validated_data["password"],
            serializer.validated_data["new_password"],
        )
        return Response(
            {"detail": "비밀번호 변경이 완료되었습니다."}, status=status.HTTP_200_OK
        )
