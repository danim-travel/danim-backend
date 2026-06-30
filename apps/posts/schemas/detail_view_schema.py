from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.posts.serializers.detail_serializer import PostDetailSerializer

post_detail_schema = extend_schema(
    tags=["posts"],
    summary="게시글 상세 조회",
    responses={
        200: PostDetailSerializer,
        404: OpenApiResponse(
            description="게시글을 찾을 수 없습니다.",
            examples=[
                OpenApiExample(
                    "게시글 없음",
                    value={"error_detail": "게시글을 찾을 수 없습니다."},
                    response_only=True,
                )
            ],
        ),
    },
)
