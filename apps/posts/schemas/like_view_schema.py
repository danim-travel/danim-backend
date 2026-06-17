from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

post_like_schema = extend_schema(
    tags=["posts"],
    summary="게시글 좋아요",
    responses={
        201: OpenApiResponse(
            description="게시글 좋아요 성공",
            examples=[
                OpenApiExample(
                    "좋아요 성공",
                    value={"is_liked": True, "like_count": 5},
                    response_only=True,
                )
            ],
        ),
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
            examples=[
                OpenApiExample(
                    "인증 실패",
                    value={"error_detail": "로그인이 필요합니다."},
                    response_only=True,
                )
            ],
        ),
        404: OpenApiResponse(
            description="해당 게시글을 찾을 수 없습니다.",
            examples=[
                OpenApiExample(
                    "게시글 없음",
                    value={"error_detail": "해당 게시글을 찾을 수 없습니다."},
                    response_only=True,
                )
            ],
        ),
        409: OpenApiResponse(
            description="이미 좋아요한 게시글입니다.",
            examples=[
                OpenApiExample(
                    "중복 좋아요",
                    value={"error_detail": {"field_name": ["like"]}},
                    response_only=True,
                )
            ],
        ),
    },
)

post_unlike_schema = extend_schema(
    tags=["posts"],
    summary="게시글 좋아요 취소",
    responses={
        200: OpenApiResponse(
            description="게시글 좋아요 취소 성공",
            examples=[
                OpenApiExample(
                    "좋아요 취소 성공",
                    value={"is_liked": False, "like_count": 4},
                    response_only=True,
                )
            ],
        ),
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
            examples=[
                OpenApiExample(
                    "인증 실패",
                    value={"error_detail": "로그인이 필요합니다."},
                    response_only=True,
                )
            ],
        ),
        404: OpenApiResponse(
            description="해당 게시글을 찾을 수 없습니다.",
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
