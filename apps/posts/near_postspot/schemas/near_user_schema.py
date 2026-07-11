from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.posts.near_postspot.serializers import (
    NearUserQuerySerializer,
    NearUserResponseSerializer,
)

near_user_schema = extend_schema(
    parameters=[NearUserQuerySerializer],
    responses={
        200: NearUserResponseSerializer,
        400: OpenApiResponse(description="이 필드는 필수 필드입니다."),
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
    tags=["near_postspot"],
    description="유저 현재 위치 주변 게시글 조회 api",
)
