from typing import Any

from django.core.cache import cache
from django.db.models import Q

from apps.core.exceptions.exception import ValidationException
from apps.explores.services.response_base import build_feed, page_from_ids
from apps.posts.models import Post, PostSpot

REGION_TTL = 60 * 30  # feed.py CACHE_TTL과 동일 — 신규 게시글 반영 지연 최소화
PAGE_LIMIT = 10
REGION_RESULT_LIMIT = 200  # 캐시에 담아둘 최대 게시글 수
REGION_KEY_VERSION = "v1"  # 그룹핑/정렬 로직 변경 시 올려서 캐시를 무효화한다

# 행정구역 개편으로 신구 명칭이 섞여 있을 수 있어(강원도->강원특별자치도 등) 둘 다 매칭한다.
# Kakao가 시도명을 축약형으로 줄 때도 있어(예: "전북 완주군...", "경기 성남시...") 정식명 옆에
# 축약형도 함께 나열한다. 방위 도(道) 이름(충남/충북/전남/전북/경남/경북)은 축약형이 정식명의
# 문자열 접두어가 아니라서(예: "충청남도"는 "충남"으로 시작하지 않음) 반드시 별도 항목으로 추가해야 한다.
REGION_PREFIXES: dict[str, list[str]] = {
    "서울": ["서울특별시", "서울"],
    "경기": ["경기도", "경기"],
    "인천": ["인천광역시", "인천"],
    "강원": ["강원도", "강원특별자치도", "강원"],
    "충청": [
        "대전광역시",
        "대전",
        "세종특별자치시",
        "세종",
        "충청남도",
        "충남",
        "충청북도",
        "충북",
    ],
    "전라": [
        "광주광역시",
        "광주",
        "전라남도",
        "전남",
        "전라북도",
        "전북특별자치도",
        "전북",
    ],
    "경상": [
        "대구광역시",
        "대구",
        "부산광역시",
        "부산",
        "울산광역시",
        "울산",
        "경상북도",
        "경북",
        "경상남도",
        "경남",
    ],
    "제주": ["제주특별자치도", "제주도", "제주"],
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

    ids = list(
        Post.objects.filter(id__in=candidate_post_ids)
        .order_by("-like_count", "-comment_count", "-id")
        .values_list("id", flat=True)[:REGION_RESULT_LIMIT]
    )

    cache.set(key, ids, REGION_TTL)
    return ids


def _region_key(region: str) -> str:
    return f"region:{REGION_KEY_VERSION}:{region}"
