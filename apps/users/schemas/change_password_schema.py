from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.change_password_serializer import (
    ChangePasswordRequestSerializer,
)

change_password_schema = extend_schema(
    tags=["users"],
    summary="비밀번호 변경",
    description=(
        "현재 비밀번호 확인 후 새 비밀번호로 변경합니다. "
        "Authorization 헤더의 access_token(Bearer) 인증이 필요합니다. "
        "소셜 로그인 유저는 변경할 수 없습니다."
    ),
    request=ChangePasswordRequestSerializer,
    responses={
        200: inline_serializer(
            name="ChangePasswordResponse",
            fields={
                "detail": serializers.CharField(default="비밀번호 변경이 완료되었습니다.")
            },
        ),
        400: OpenApiResponse(description="현재 비밀번호가 틀렸습니다."),
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        403: OpenApiResponse(
            description="소셜 로그인 유저는 비밀번호를 변경할 수 없습니다."
        ),
    },
)
