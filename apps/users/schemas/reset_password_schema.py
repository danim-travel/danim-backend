from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.reset_password_serializer import (
    ResetPasswordRequestSerializer,
)

reset_password_schema = extend_schema(
    tags=["users"],
    summary="비밀번호 재설정",
    description=(
        "이메일 인증(verify-email)으로 발급받은 email_token으로 비밀번호를 재설정합니다. "
        "로그인 없이 호출하며, 토큰에 담긴 이메일의 유저 비밀번호를 새 값으로 변경합니다. "
        "토큰은 1회용입니다."
    ),
    request=ResetPasswordRequestSerializer,
    responses={
        200: inline_serializer(
            name="ResetPasswordResponse",
            fields={
                "detail": serializers.CharField(
                    default="비밀번호 재설정이 완료되었습니다."
                )
            },
        ),
        400: OpenApiResponse(description="새 비밀번호 형식이 올바르지 않습니다."),
        401: OpenApiResponse(description="유효하지 않은 토큰입니다."),
    },
)
