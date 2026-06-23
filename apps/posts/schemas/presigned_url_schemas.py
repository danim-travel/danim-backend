from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view

from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)

post_presigned_schema = extend_schema_view(
    post=extend_schema(
        tags=["posts"],
        summary="게시글 이미지 업로드용 presigned URL 발급",
        description=(
            "게시글 이미지를 S3에 직접 업로드하기 위한 presigned URL을 발급합니다.\n"
            "- 프론트는 presigned_url로 S3에 직접 PUT 업로드\n"
            "- 업로드 후 key를 게시글 작성 API에 전달\n"
            "- 허용 확장자: .jpg, .jpeg, .png, .webp"
        ),
        request=PresignedUrlRequestSerializer,
        responses={
            200: PresignedUrlResponseSerializer,
            400: OpenApiResponse(description="지원하지 않는 파일 형식입니다."),
            401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않습니다."),
        },
    )
)
