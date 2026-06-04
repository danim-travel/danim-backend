from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from apps.users.serializers.token_serializer import TokenResponseSerializer

token_refresh_schema = extend_schema(
    tags=["users"],
    summary="액세스 토큰 재발급",
    description=(
        "httpOnly 쿠키의 refresh_token으로 새로운 access_token을 발급합니다. "
        "access_token은 응답 body로 내려갑니다."
    ),
    parameters=[
        OpenApiParameter(
            name="refresh_token",
            location=OpenApiParameter.COOKIE,
            required=True,
            description="로그인 시 발급된 httpOnly refresh_token 쿠키",
        ),
    ],
    responses={
        200: TokenResponseSerializer,
        403: OpenApiResponse(
            description="refresh_token이 없거나 만료/손상되었거나 로그아웃된 토큰입니다."
        ),
    },
)
