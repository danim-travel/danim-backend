from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.posts.near_postspot.serializers import (
    NearPostQuerySerializer,
    NearPostResponseSerializer,
)

near_post_schema = extend_schema(
    parameters=[NearPostQuerySerializer],
    responses={
        200: NearPostResponseSerializer,
        400: OpenApiResponse(description="이 필드는 필수 필드입니다."),
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
    tags=["near_postspots"],
    summary="유저가 클릭한 게시글의 spot 주변의 게시글 조회 api",
)
