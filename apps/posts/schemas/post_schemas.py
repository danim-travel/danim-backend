from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.posts.serializers import PostCreateRequestSerializer

post_create_schema = extend_schema(
    request=PostCreateRequestSerializer,
    responses={
        201: OpenApiResponse(description="게시글이 작성되었습니다."),
        400: OpenApiResponse(description="이 필드는 필수 항목입니다."),
        401: OpenApiResponse(description="인증되지 않은 사용자입니다."),
    },
    tags=["posts"],
    summary="게시글 생성",
)
