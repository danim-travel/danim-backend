from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.posts.serializers.update_serializer import PostUpdateSerializer

post_update_schema = extend_schema(
    tags=["posts"],
    summary="게시글 수정",
    description="본인의 게시글을 부분 수정합니다. 보낸 필드만 갱신됩니다.",
    request=PostUpdateSerializer,
    responses={
        200: OpenApiResponse(
            description="게시글이 수정되었습니다.",
            examples=[
                OpenApiExample(
                    "수정 성공",
                    value={"detail": "게시글이 수정되었습니다."},
                    response_only=True,
                )
            ],
        ),
        400: OpenApiResponse(
            description="유효하지 않은 필드입니다.",
            examples=[
                OpenApiExample(
                    "유효성 검사 실패",
                    value={"error_detail": {"title": ["유효하지 않은 필드입니다."]}},
                    response_only=True,
                )
            ],
        ),
        401: OpenApiResponse(
            description="인증되지 않은 사용자입니다.",
            examples=[
                OpenApiExample(
                    "인증 실패",
                    value={"error_detail": "인증되지 않은 사용자입니다."},
                    response_only=True,
                )
            ],
        ),
        404: OpenApiResponse(
            description="게시글을 찾을 수 없습니다. (존재하지 않거나 본인의 게시글이 아닌 경우)",
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
