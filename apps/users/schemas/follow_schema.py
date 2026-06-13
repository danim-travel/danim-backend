from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from apps.users.serializers.follow_serializer import FollowerResponseSerializer

follower_list_schema = extend_schema(
    tags=["follows"],
    summary="팔로워 목록 조회",
    description=(
        "특정 유저의 팔로워(그 유저를 팔로우하는 사람들) 목록을 커서 페이지네이션으로 조회합니다.\n\n"
        "- `is_following`은 요청한 유저가 목록의 각 유저를 팔로우 중인지 여부입니다.\n"
        "- 존재하지 않는 user_id는 404로 응답합니다."
    ),
    parameters=[
        OpenApiParameter(
            name="cursor",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
            description="다음 페이지 커서 (응답의 next에서 추출)",
        ),
        OpenApiParameter(
            name="page_size",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
            description="페이지 크기 (기본 10, 최대 100)",
        ),
    ],
    responses={
        200: FollowerResponseSerializer,
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
        404: OpenApiResponse(description="존재하지 않는 유저입니다."),
    },
)
