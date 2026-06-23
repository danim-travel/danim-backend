from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.users.serializers.me_serializer import (
    UserDeleteRequestSerializer,
    UserInfoResponseSerializer,
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

user_me_schema = extend_schema(
    tags=["users"],
    summary="내 정보 조회",
    description="로그인한 본인의 정보를 조회합니다.",
    responses={
        200: UserInfoResponseSerializer,
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
    },
)

user_delete_schema = extend_schema(
    tags=["users"],
    summary="회원탈퇴",
    description=(
        "로그인한 본인의 계정을 삭제합니다. "
        "본문에 현재 비밀번호(password)를 받아 검증 후 탈퇴 처리하며, "
        "성공 시 204 No Content(본문 없음)를 반환합니다."
    ),
    request=UserDeleteRequestSerializer,
    responses={
        204: OpenApiResponse(description="회원탈퇴 성공 (응답 본문 없음)"),
        400: OpenApiResponse(description="비밀번호를 입력해주세요."),
        401: OpenApiResponse(
            description="비밀번호가 틀립니다. / 자격 인증 데이터가 제공되지 않았습니다."
        ),
    },
)
