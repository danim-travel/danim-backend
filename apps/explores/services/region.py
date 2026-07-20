from typing import Any

from django.core.cache import cache
from django.db.models import Q

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.dtos import ExploreRes
from apps.posts.models import Post, PostSpot

REGION_TTL = 60 * 60 * 24
PAGE_LIMIT = 10
REGION_CANDIDATE_LIMIT = 5_000  # PostSpot 후보 조회 IN절 폭주 방지
REGION_RESULT_LIMIT = 200  # 캐시에 담아둘 최대 게시글 수
REGION_KEY_VERSION = "v1"  # 그룹핑/정렬 로직 변경 시 올려서 캐시를 무효화한다

# 행정구역 개편으로 신구 명칭이 섞여 있을 수 있어(강원도->강원특별자치도 등) 둘 다 매칭한다.
REGION_PREFIXES: dict[str, list[str]] = {
    "서울": ["서울특별시"],
    "경기": ["경기도"],
    "인천": ["인천광역시"],
    "강원": ["강원도", "강원특별자치도"],
    "충청": ["대전광역시", "세종특별자치시", "충청남도", "충청북도"],
    "전라": ["광주광역시", "전라남도", "전라북도", "전북특별자치도"],
    "경상": ["대구광역시", "부산광역시", "울산광역시", "경상북도", "경상남도"],
    "제주": ["제주특별자치도", "제주도"],
}


def feeds_for_region(region: str, cursor: str | None) -> tuple[Any, Any, Any]:
    """지역 필터 목록 조회. 인기순(좋아요/댓글) 정렬, post_id 기반 커서 페이지네이션."""
    seed = 0
    prefixes = REGION_PREFIXES.get(region)
    if prefixes is None:
        raise ValidationException("지원하지 않는 지역입니다.")

    ids = _region_post_ids(region, prefixes)

    if cursor:
        try:
            start = ids.index(cursor) + 1
        except ValueError:
            raise ValidationException("잘못된 커서값입니다.")
    else:
        start = 0

    page_ids = ids[start : start + PAGE_LIMIT]
    if not page_ids:
        return [], None, seed

    new_cursor = encode_cursor(page_ids[-1])
    queryset = Post.objects.filter(id__in=page_ids)
    rank = {pid: i for i, pid in enumerate(page_ids)}
    posts = sorted(queryset, key=lambda p: rank[p.id])

    feed = [
        ExploreRes(
            id=p.id,
            thumbnail=s3_svc.create_download_presigned_url(p.thumbnail),
            thumbnail_width=p.thumbnail_width,
            thumbnail_height=p.thumbnail_height,
            like_count=p.like_count,
            comment_count=p.comment_count,
        )
        for p in posts
    ]
    return feed, new_cursor, seed


def _region_post_ids(region: str, prefixes: list[str]) -> list[str]:
    """redis에서 지역별 인기순 post id 배열을 불러오거나, 없으면 만들어서 저장."""
    key = _region_key(region)
    cached = cache.get(key)
    if cached is not None:
        return cached

    # 상관 서브쿼리 대신 독립 쿼리 1번으로 후보 post_id를 먼저 뽑아 재사용한다
    # (explore 검색에서 같은 이유로 이미 채택한 패턴 — 게시글별 반복 서브플랜 방지).
    match = Q()
    for prefix in prefixes:
        match |= Q(location__road_address_name__startswith=prefix) | Q(
            location__address_name__startswith=prefix
        )
    candidate_ids = set(
        PostSpot.objects.filter(match).values_list("post_id", flat=True)[
            :REGION_CANDIDATE_LIMIT
        ]
    )

    ids: list[str] = []
    if candidate_ids:
        ids = list(
            Post.objects.filter(id__in=candidate_ids)
            .order_by("-like_count", "-comment_count", "-id")
            .values_list("id", flat=True)[:REGION_RESULT_LIMIT]
        )

    cache.set(key, ids, REGION_TTL)
    return ids


def _region_key(region: str) -> str:
    return f"region:{REGION_KEY_VERSION}:{region}"
