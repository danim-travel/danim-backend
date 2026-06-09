from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
    CommentListSerializer,
    CommentListSwaggerSerializer,
    CommentUpdateResponseSerializer,
)
from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)

comment_create_schema = extend_schema(
    request=CommentCreateSerializer,
    responses={
        201: CommentCreateResponseSerializer,
        400: OpenApiResponse(
            description="content와 comment_img 두 항목이 입력해야합니다.",
        ),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(
            description="게시글에 대한 정보를 찾지 못했습니다.",
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
            description="게시글에 대한 정보를 찾지 못했습니다.",
        ),
    },
    tags=["comments"],
    summary="댓글 목록 조회",
)
comment_update_schema = extend_schema(
    request=CommentUpdateResponseSerializer,
    responses={
        200: CommentUpdateResponseSerializer,
        400: OpenApiResponse(
            description="이 필드의 글자 수가 100이하인지 확인하십시오.",
        ),
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
        ),
        403: OpenApiResponse(
            description="본인이 작성한 댓글만 수정 할 수 있습니다.",
        ),
        404: OpenApiResponse(
            description="댓글에 대한 정보를 찾지 못했습니다.",
        ),
    },
    tags=["comments"],
    summary="댓글 수정",
)
comment_delete_schema = extend_schema(
    responses={
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
        ),
        403: OpenApiResponse(
            description="본인이 작성한 댓글만 삭제 할 수 있습니다.",
        ),
        404: OpenApiResponse(
            description="댓글에 대한 정보를 찾지 못했습니다.",
        ),
    },
    tags=["comments"],
    summary="댓글 삭제",
)
comment_presigned_urls_schema = extend_schema(
    request=PresignedUrlRequestSerializer,
    responses={
        200: PresignedUrlResponseSerializer,
        400: OpenApiResponse(
            description="지원하지 않는 파일 형식입니다.",
        ),
        401: OpenApiResponse(
            description="로그인이 필요합니다.",
        ),
    },
    tags=["comments"],
    summary="댓글 presigned_url 발급",
)
