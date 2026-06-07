from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.users.serializers.user_update_delete_serializer import (
    UserUpdateRequestSerializer,
    UserUpdateResponseSerializer,
)

user_update_schema = extend_schema(
    tags=["users"],
    summary="회원정보 수정",
    description=(
        "로그인한 본인의 정보를 부분 수정합니다. "
        "nickname, intro, key(프로필 이미지 S3 객체 키)를 선택적으로 받으며, "
        "보낸 필드만 갱신됩니다."
    ),
    request=UserUpdateRequestSerializer,
    responses={
        200: UserUpdateResponseSerializer,
        400: OpenApiResponse(description="입력값 검증 실패 (닉네임 형식 등)"),
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        409: OpenApiResponse(description="이미 존재하는 닉네임입니다."),
    },
)
