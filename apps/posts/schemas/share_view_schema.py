from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

post_share_schema = extend_schema(
    tags=["posts"],
    summary="게시글 공유",
    responses={
        200: OpenApiResponse(
            description="게시글 공유 성공",
            examples=[
                OpenApiExample(
                    "공유 성공",
                    value={"redirect_url": "https://{domain}/api/v1/posts/uuid"},
                    response_only=True,
                )
            ],
        ),
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
