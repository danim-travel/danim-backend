from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.users.serializers.token_serializer import (
    TokenRequestSerializer,
    TokenResponseSerializer,
)

token_refresh_schema = extend_schema(
    tags=["users"],
    summary="액세스 토큰 재발급",
    description=(
        "refresh_token을 받아 새로운 access_token을 발급합니다. "
        "access_token은 응답 body, refresh_token은 httpOnly 쿠키로 내려갑니다."
    ),
    request=TokenRequestSerializer,
    responses={
        200: TokenResponseSerializer,
        400: OpenApiResponse(description="refresh_token이 누락되었습니다."),
        403: OpenApiResponse(
            description="로그인 세션이 만료되었습니다. (refresh_token 만료/손상)"
        ),
    },
)
