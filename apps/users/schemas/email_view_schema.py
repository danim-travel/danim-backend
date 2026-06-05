from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.email_serializer import (
    EmailSendSerializer,
    EmailVerifySerializer,
)

email_send_schema = extend_schema(
    tags=["users"],
    summary="이메일 인증코드 발송",
    description="이메일과 목적(purpose)을 받아 인증코드 6자리를 메일로 발송합니다.",
    request=EmailSendSerializer,
    responses={
        200: inline_serializer(
            name="EmailSendResponse",
            fields={
                "detail": serializers.CharField(
                    default="이메일 인증 코드가 전송되었습니다."
                )
            },
        ),
        400: OpenApiResponse(
            description="이메일 형식이 올바르지 않거나 purpose 값이 잘못되었습니다."
        ),
        500: OpenApiResponse(description="서버 오류로 인증코드 저장에 실패했습니다."),
        502: OpenApiResponse(description="이메일 발송에 실패했습니다."),
    },
)

email_verify_schema = extend_schema(
    tags=["users"],
    summary="이메일 인증코드 검증",
    description="이메일·목적·인증코드를 검증하고, 성공 시 회원가입에 사용할 email_token을 반환합니다.",
    request=EmailVerifySerializer,
    responses={
        200: inline_serializer(
            name="EmailVerifyResponse",
            fields={
                "detail": serializers.CharField(default="이메일이 인증 되었습니다."),
                "email_token": serializers.CharField(),
            },
        ),
        400: OpenApiResponse(
            description="인증 코드가 만료되었거나 존재하지 않거나 틀렸습니다."
        ),
        500: OpenApiResponse(description="서버 오류로 인증 처리에 실패했습니다."),
    },
)
