from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

post_delete_schema = extend_schema(
    tags=["posts"],
    summary="게시글 삭제",
    description="본인의 게시글을 삭제합니다.",
    responses={
        200: OpenApiResponse(
            description="게시글이 삭제되었습니다.",
            examples=[
                OpenApiExample(
                    "삭제 성공",
                    value={"detail": "게시글이 삭제되었습니다."},
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
