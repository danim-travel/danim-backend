from typing import Any

from django.core.cache import cache
from django.db.models import Q

from apps.core.exceptions.exception import ValidationException
from apps.explores.services.feed_builder import build_feed, page_from_ids
from apps.explores.services.response_base import PAGE_SIZE as PAGE_LIMIT
from apps.posts.models import Post, PostSpot

REGION_TTL = 60 * 30  # feed.py CACHE_TTL과 동일 — 신규 게시글 반영 지연 최소화
REGION_RESULT_LIMIT = 200  # 캐시에 담아둘 최대 게시글 수
REGION_KEY_VERSION = "v1"  # 그룹핑/정렬 로직 변경 시 올려서 캐시를 무효화한다

# 행정구역 개편으로 신구 명칭이 섞여 있을 수 있어(강원도->강원특별자치도 등) 둘 다 매칭한다.
# Kakao가 시도명을 축약형으로 줄 때도 있어(예: "전북 완주군...", "경기 성남시...") 정식명 옆에
# 축약형도 함께 나열한다.
#
# 다만 축약형이 정식명의 "문자열 접두어"인 경우엔 정식명 항목이 잉여이므로 뺐다
# (istartswith("부산")이 "부산광역시…"를 이미 덮음 -> 서울/경기/인천/강원/광주/대전/세종/
# 대구/부산/울산/제주/전북(신명칭)이 여기 해당).
# 방위 도(道)의 옛 정식명(충청남도/충청북도/전라남도/전라북도/경상북도/경상남도)은
# 축약형이 접두어가 아니므로(예: "충청남도"는 "충남"으로 시작하지 않음) 반드시 별도 항목으로
# 남겨야 한다 — 이걸 "충남과 중복"이라 보고 지우면 신구 명칭 혼용 매칭이 조용히 깨진다.
REGION_PREFIXES: dict[str, list[str]] = {
    "서울": ["서울"],
    "경기": ["경기"],
    "인천": ["인천"],
    "강원": ["강원"],
    "충청": ["대전", "세종", "충청남도", "충남", "충청북도", "충북"],
    "전라": ["광주", "전라남도", "전남", "전라북도", "전북"],
    "경상": ["대구", "부산", "울산", "경상북도", "경북", "경상남도", "경남"],
    "제주": ["제주"],
}


def feeds_for_region(region: str, cursor: str | None) -> tuple[Any, Any, Any]:
    """지역 필터 목록 조회. 인기순(좋아요/댓글) 정렬, post_id 기반 커서 페이지네이션."""
    seed = 0
    prefixes = REGION_PREFIXES.get(region)
    if prefixes is None:
        raise ValidationException("지원하지 않는 지역입니다.")

    ids = _region_post_ids(region, prefixes)
    page_ids, new_cursor = page_from_ids(ids, cursor, PAGE_LIMIT)
    if not page_ids:
        return [], None, seed

    feed = build_feed(page_ids)
    return feed, new_cursor, seed


def _region_post_ids(region: str, prefixes: list[str]) -> list[str]:
    """redis에서 지역별 인기순 post id 배열을 불러오거나, 없으면 만들어서 저장."""
    key = _region_key(region)
    cached = cache.get(key)
    if cached is not None:
        return cached

    match = Q()
    for prefix in prefixes:
        match |= Q(location__road_address_name__istartswith=prefix) | Q(
            location__address_name__istartswith=prefix
        )
    candidate_post_ids = PostSpot.objects.filter(match).order_by().values("post_id")

    # TRADE-OFF: posts에 (like_count, comment_count, id) 복합 인덱스가 없어
    # 캐시 미스마다 지역 후보 전량을 정렬한다. 지역 8개 x 30분 TTL이라 당장은
    # 감내 가능하지만, 키 만료 순간 여러 요청이 몰리면(cache stampede) 무방비다
    # (feed.py/search.py와 동일 패턴). 트래픽이 늘면 인덱스 추가를 검토할 것.
    ids = list(
        Post.objects.filter(id__in=candidate_post_ids)
        .order_by("-like_count", "-comment_count", "-id")
        .values_list("id", flat=True)[:REGION_RESULT_LIMIT]
    )

    cache.set(key, ids, REGION_TTL)
    return ids


def _region_key(region: str) -> str:
    return f"region:{REGION_KEY_VERSION}:{region}"
