from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.explores.serializers import ExploreQuerySerializer, ExploreResponseSerializer

explore_schema = extend_schema(
    tags=["explores"],
    summary="탐색 피드 및 검색/지역 목록 조회",
    description=(
        "탐색 탭의 추천 피드를 조회하거나, search/region 값이 주어지면 해당 결과를 반환합니다."
        "우선순위: search > region > 추천 피드 순으로 하나만 적용됩니다."
        "검색: search 값이 있을 때 동작하며, 커서는 post_id(Base64) 기반으로 동작합니다."
        "지역: region 값이 있을 때 동작하며(서울/경기/인천/강원/충청/전라/경상/제주), "
        "인기순(좋아요·댓글순)으로 정렬되고 커서는 post_id(Base64) 기반으로 동작합니다."
        "추천: search/region 값이 없을 때 동작하며, 커서는 페이지 번호(int) 기반으로 동작합니다. 무작위 정렬 유지를 위해 첫 요청 시 발급된 `seed`를 다음 요청에 계속 넘겨주어야 합니다."
    ),
    parameters=[ExploreQuerySerializer],
    responses={
        200: ExploreResponseSerializer,
        400: OpenApiResponse(
            description="잘못된 커서값이거나 필수 인자가 유효하지 않습니다."
        ),
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않았습니다."),
    },
)
