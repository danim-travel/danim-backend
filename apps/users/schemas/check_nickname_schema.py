from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.check_nickname_serializer import CheckNicknameSerializer

user_check_nickname_schema = extend_schema(
    tags=["users"],
    summary="닉네임 중복 확인",
    description="닉네임 형식 검증 및 중복 여부 확인",
    request=CheckNicknameSerializer,
    responses={
        200: inline_serializer(
            name="CheckNicknameResponse",
            fields={"detail": serializers.CharField(default="사용가능한 닉네임 입니다.")},
        ),
        400: OpenApiResponse(description="닉네임은 필수 항목입니다."),
        409: OpenApiResponse(description="중복된 닉네임 입니다."),
    },
)
