from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
    CommentListSerializer,
    CommentListSwaggerSerializer,
)

comment_create_schema = extend_schema(
    request=CommentCreateSerializer,
    responses={
        201: CommentCreateResponseSerializer,
        400: OpenApiResponse(
            description='{"error_detail" : ["content와 comment_img 두 항목 하나는 입력해야 합니다"],"status_code" : 400}\n {"error_detail" : "content는 100자 이하로 작성되어야합니다.","status_code" : 400}',
        ),
        401: OpenApiResponse(
            description='{"error_detail" : "로그인이 필요합니다.","status_code" : 401}'
        ),
        404: OpenApiResponse(
            description='{"error_detail" : "게시글에 대한 정보를 찾지 못했습니다.","status_code" : 404}}'
        ),
    },
    tags=["comments"],
    summary="댓글 생성",
)
comment_list_schema = extend_schema(
    parameters=[CommentListSwaggerSerializer],
    responses={
        200: CommentListSerializer,
        404: OpenApiResponse(
            description='{"error_detail" : "게시글에 대한 정보를 찾지 못했습니다.","status_code" : 404}"}'
        ),
    },
    tags=["comments"],
    summary="댓글 목록 조회",
)
