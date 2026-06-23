from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.posts.serializers.main_list_serializer import PostMainListSerializer

post_main_list_schema = extend_schema(
    tags=["posts"],
    summary="게시글 메인 리스트 조회",
    responses={
        200: PostMainListSerializer,
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
