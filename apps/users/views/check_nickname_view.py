from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.schemas.check_nickname_schema import user_check_nickname_schema
from apps.users.serializers.check_nickname_serializer import CheckNicknameSerializer
from apps.users.services.check_nickname_service import CheckNicknameService


class CheckNicknameView(APIView):
    permission_classes = [AllowAny]
    service = CheckNicknameService()

    @user_check_nickname_schema
    def post(self, request: Request) -> Response:
        serializer = CheckNicknameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        self.service.check_duplicate_nickname(serializer.validated_data["nickname"])

        return Response(
            {"detail": "사용가능한 닉네임 입니다."}, status=status.HTTP_200_OK
        )
