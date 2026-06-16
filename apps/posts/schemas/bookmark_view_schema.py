from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

bookmark_create_schema = extend_schema(
    tags=["posts"],
    summary="게시글 북마크 추가",
    responses={
        201: OpenApiResponse(
            description="북마크가 추가되었습니다.",
            examples=[
                OpenApiExample(
                    "북마크 성공",
                    value={"is_bookmarked": True},
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
            description="게시글을 찾을 수 없습니다.",
            examples=[
                OpenApiExample(
                    "게시글 없음",
                    value={"error_detail": "해당 게시글을 찾을 수 없습니다."},
                    response_only=True,
                )
            ],
        ),
        409: OpenApiResponse(
            description="이미 북마크한 게시글입니다.",
            examples=[
                OpenApiExample(
                    "중복 북마크",
                    value={"error_detail": "이미 북마크한 게시글입니다."},
                    response_only=True,
                )
            ],
        ),
    },
)

bookmark_delete_schema = extend_schema(
    tags=["posts"],
    summary="게시글 북마크 취소",
    responses={
        200: OpenApiResponse(
            description="북마크가 취소되었습니다.",
            examples=[
                OpenApiExample(
                    "북마크 취소 성공",
                    value={"is_bookmarked": False},
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
            description="게시글을 찾을 수 없습니다.",
            examples=[
                OpenApiExample(
                    "게시글 없음",
                    value={"error_detail": "해당 게시글을 찾을 수 없습니다."},
                    response_only=True,
                )
            ],
        ),
    },
)
