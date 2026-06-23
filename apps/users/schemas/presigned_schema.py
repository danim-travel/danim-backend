from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)

from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)

# UserProfileImgView.post는 베이스(PresignedUrlView)에서 상속받으므로
# 메서드 데코레이터 대신 extend_schema_view로 클래스에 스키마를 적용한다.
user_profile_presigned_schema = extend_schema_view(
    post=extend_schema(
        tags=["users"],
        summary="프로필 이미지 업로드용 presigned URL 발급",
        description=(
            "프로필 이미지를 S3에 직접 업로드하기 위한 presigned URL을 발급합니다.\n\n"
            "- 프론트는 응답의 `presigned_url`로 S3에 직접 PUT 업로드합니다.\n"
            "- 업로드 후 `key`를 회원정보 수정 API에 전달해 저장합니다.\n"
            "- presigned URL 유효시간: 900초(15분)\n"
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
