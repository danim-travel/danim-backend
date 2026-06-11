from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.users.serializers.profile_serializer import ProfileResponseSerializer

user_profile_schema = extend_schema(
    tags=["users"],
    summary="프로필 조회",
    description=(
        "특정 유저의 프로필을 조회합니다.\n\n"
        "- 팔로워/팔로잉 수, 게시물 수, 게시물 목록을 포함합니다.\n"
        "- `is_following`은 요청한 유저가 해당 프로필 유저를 팔로우 중인지 여부입니다.\n"
        "- 존재하지 않는 user_id(형식 오류 포함)는 404로 응답합니다."
    ),
    responses={
        200: ProfileResponseSerializer,
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        404: OpenApiResponse(description="존재하지 않는 유저입니다."),
    },
)
