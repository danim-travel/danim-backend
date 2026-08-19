from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

bookmark_list_schema = extend_schema(
    tags=["posts"],
    summary="북마크 리스트 조회",
    description="로그인한 유저가 북마크한 게시글 목록을 최근 북마크순으로 조회 (커서 페이지네이션)",
    responses={
        200: OpenApiResponse(
            description="북마크 리스트 조회 성공",
            examples=[
                OpenApiExample(
                    "조회 성공",
                    value={
                        "next": (
                            "https://dev-api.danim.kr/api/v1/posts/bookmark"
                            "?cursor=cD0wMUtUVFZWRlFKU0c2NloyRFpIVDFKRDJGUg=="
                        ),
                        "results": [
                            {
                                "post_id": "01JWNZ8KQE4VXRM2P7HFGB3YDN",
                                "thumbnail": "https://s3.ap-northeast-2.amazonaws.com/danim/posts/thumbnail.png",
                                "thumbnail_width": 1080,
                                "thumbnail_height": 1350,
                                "description": "깽깽이 발로 갈까요.",
                                "comment_count": 3,
                                "is_liked": False,
                                "like_count": 10,
                            }
                        ],
                    },
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
    },
)
