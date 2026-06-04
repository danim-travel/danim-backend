from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.schemas import email_send_schema, email_verify_schema
from apps.users.serializers.email_serializer import (
    EmailSendSerializer,
    EmailVerifySerializer,
)
from apps.users.services.email_service import EmailService


class EmailSendView(APIView):
    """
    POST api/v1/users/verification/send-email
    이메일 발송에 관한 class
    """

    permission_classes = [AllowAny]
    service = EmailService()

    @email_send_schema
    def post(self, request: Request) -> Response:
        """이메일 및 목적을 보내주면 인증코드 숫자 6자리를 보내주는 view"""
        serializer = EmailSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.send_email(
            email=serializer.validated_data["email"],
            purpose=serializer.validated_data["purpose"],
        )
        return Response(
            {"detail": "이메일 인증 코드가 전송되었습니다."}, status=status.HTTP_200_OK
        )


class EmailVerifyView(APIView):
    """
    POST api/v1/users/verification/verify-email
    이메일 인증에 관련된 class
    """

    permission_classes = [AllowAny]
    service = EmailService()

    @email_verify_schema
    def post(self, request: Request) -> Response:
        """이메일과 인증코드를 검증하고 email_token을 반환하는 view"""
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_token = self.service.verify_code(
            email=serializer.validated_data["email"],
            purpose=serializer.validated_data["purpose"],
            code=serializer.validated_data["code"],
        )
        return Response(
            {
                "detail": "이메일이 인증 되었습니다.",
                "email_token": email_token,
            },
            status=status.HTTP_200_OK,
        )
