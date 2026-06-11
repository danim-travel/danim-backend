from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.posts.serializers.create_serializer import PostCreateSerializer

post_create_schema = extend_schema(
    tags=["posts"],
    summary="게시글 작성",
    description=(
        "게시글을 작성합니다.\n\n"
        "- `title`은 필수, `description`/`thumbnail`/`spots`는 선택입니다.\n"
        "- `thumbnail`, `spots[].images[].key`는 presigned-url API로 미리 업로드한 "
        "S3 객체 키를 전달합니다.\n"
        "- `spots`는 방문 순서(`order`), 위치(`location`), 이미지(`images`)를 포함합니다."
    ),
    request=PostCreateSerializer,
    responses={
        201: OpenApiResponse(
            description="게시글 작성 성공",
            examples=[
                OpenApiExample(
                    "작성 성공",
                    value={"detail": "게시글이 작성되었습니다."},
                    response_only=True,
                )
            ],
        ),
        400: OpenApiResponse(
            description="입력값 검증 실패 (예: title 누락 등)",
            examples=[
                OpenApiExample(
                    "검증 실패",
                    value={
                        "error_detail": {"title": ["이 필드는 필수 항목입니다."]},
                        "status_code": 400,
                    },
                    response_only=True,
                )
            ],
        ),
        401: OpenApiResponse(description="인증되지 않은 사용자입니다."),
    },
)
