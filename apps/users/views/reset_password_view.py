from rest_framework.request import Request

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.users.schemas.reset_password_schema import reset_password_schema
from apps.users.serializers.reset_password_serializer import ResetPasswordRequestSerializer

from apps.users.services.reset_password_service import ResetPasswordService
from rest_framework import status

class ResetPasswordView(APIView):
    permission_classes = [AllowAny,]
    service = ResetPasswordService()

    @reset_password_schema
    def post(self,request:Request)->Response:
        serializer = ResetPasswordRequestSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)

        self.service.reset_password(
            serializer.validated_data["email_token"],
            serializer.validated_data["new_password"],
        )
        return Response({"detail":"비밀번호 재설정이 완료되었습니다."},status=status.HTTP_200_OK)

