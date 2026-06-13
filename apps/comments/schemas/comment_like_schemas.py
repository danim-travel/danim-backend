from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.comments.serializers import CommentLikeCreateSerializer

comment_like_create_schema = extend_schema(
    responses={
        200: CommentLikeCreateSerializer,
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
        ),
        404: OpenApiResponse(description="해당 댓글을 찾을 수 없습니다."),
        409: OpenApiResponse(description="이미 좋아요를 누른 댓글입니다."),
    },
    tags=["comment_likes"],
    summary="댓글 좋아요 생성 api",
)
