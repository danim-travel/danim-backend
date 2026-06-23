from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)

dm_presigned_url_schema = extend_schema(
    request=PresignedUrlRequestSerializer,
    responses={
        201: PresignedUrlResponseSerializer,
        400: OpenApiResponse(description="지원하지 않는 파일 형식입니다."),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="대화방을 찾을 수 없습니다."),
    },
    tags=["direct-messages"],
    summary="DM 이미지 업로드 Presigned URL 발급",
)
