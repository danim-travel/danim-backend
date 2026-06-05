from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers

from apps.users.serializers.login_logout_serializer import LoginSerializer
from apps.users.serializers.token_serializer import TokenResponseSerializer

login_schema = extend_schema(
    tags=["users"],
    summary="로그인",
    description=(
        "이메일과 비밀번호로 로그인합니다. "
        "access_token은 응답 body, refresh_token은 httpOnly 쿠키로 내려갑니다. "
        "요청에 기존 refresh_token 쿠키가 있으면 블랙리스트 처리(재로그인) 후 새 토큰을 발급합니다."
    ),
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(
            description="이메일 또는 비밀번호 형식이 올바르지 않습니다."
        ),
        401: OpenApiResponse(description="이메일 또는 비밀번호가 올바르지 않습니다."),
    },
)

logout_schema = extend_schema(
    tags=["users"],
    summary="로그아웃",
    description=(
        "httpOnly 쿠키의 refresh_token을 블랙리스트에 등록하고 쿠키를 삭제합니다. "
        "Authorization 헤더의 access_token(Bearer) 인증이 필요합니다."
    ),
    request=None,
    responses={
        200: inline_serializer(
            name="LogoutResponse",
            fields={"detail": serializers.CharField(default="로그아웃 되었습니다.")},
        ),
        400: OpenApiResponse(description="로그아웃을 위한 토큰이 없습니다."),
        401: OpenApiResponse(description="인증 정보가 없거나 유효하지 않습니다."),
    },
)
