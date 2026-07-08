import re
from typing import Any, no_type_check

from django.contrib.postgres.search import TrigramSimilarity
from django.core.cache import cache
from django.db.models import Case, Exists, F, FloatField, OuterRef, Q, Value, When
from django.db.models.expressions import Combinable

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.dtos import ExploreRes
from apps.posts.models import Post, PostSpot

SEARCH_TTL = 60 * 60 * 24
PAGE_LIMIT = 10
DESCRIPTION_SIM_LIMIT = 0.25
LOCATION_MATCH_SCORE = 3.0

_JAMO = re.compile(r"[\u3131-\u318E]")  # 한글 자음 모음 정규표현식


def feeds_for_search(search: str, cursor: str | None) -> tuple[Any, Any, Any]:
    seed = 0
    cleaned = _clean(search)
    tokens = cleaned.split()

    if not tokens or (len(tokens) == 1 and len(tokens[0]) < 2):
        return [], None, seed

    ids = _search(tokens)

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

    feed = []
    for p in posts:
        feed.append(
            ExploreRes(
                id=p.id,
                thumbnail=s3_svc.create_download_presigned_url(p.thumbnail),
                like_count=p.like_count,
                comment_count=p.comment_count,
            )
        )
    return feed, new_cursor, seed


def _clean(search: str) -> str:
    """search 중에서 _JAMO에 해당하는 문자가 있으면 빈 문자열로 치환"""
    return _JAMO.sub("", search).strip()


@no_type_check
def _search(tokens: list[Any]) -> list[Any]:
    """redis에서 post 배열을 불러오거나, 없으면 만들어서 저장"""
    key = _search_key(tokens)
    cached = cache.get(key)
    if cached is not None:
        return cached

    flt = Q()
    title_score: Combinable = Value(0.0, output_field=FloatField())
    hashtag_score: Combinable = Value(0.0, output_field=FloatField())
    description_sim: Combinable = Value(0.0, output_field=FloatField())
    location_score: Combinable = Value(0.0, output_field=FloatField())
    tri_annots: dict[str, TrigramSimilarity] = {}
    location_annots: dict[str, Exists] = {}

    for i, t in enumerate(tokens):

        # 한 게시글이 스팟(주소)을 여러 개 가질 수 있어 join 대신 Exists 로
        # "매칭되는 주소를 하나라도 갖고 있는가"만 불리언으로 확인 (row 중복 방지)
        location_match = PostSpot.objects.filter(
            post=OuterRef("pk"),
            location__road_address_name__icontains=t,
        )
        location_annots[f"location_match_{i}"] = Exists(location_match)

        # 검색어에 맞는 후보
        flt |= (
            Q(title__icontains=t)
            | Q(description__icontains=f"#{t}")
            | Q(user__nickname__icontains=t)
            # t가 보통 한글이라 annotate가 깨질까봐 i로 받음
            | Q(**{f"description_sim_{i}__gte": DESCRIPTION_SIM_LIMIT})
            | Q(**{f"location_match_{i}": True})
        )
        # 후보를 정렬할 점수
        title_score = title_score + Case(
            When(title__icontains=t, then=Value(3.0)),
            default=Value(0.0),
            output_field=FloatField(),
        )
        hashtag_score = hashtag_score + Case(
            When(description__icontains=f"#{t}", then=Value(3.0)),
            default=Value(0.0),
            output_field=FloatField(),
        )
        trigram = TrigramSimilarity("description", t)
        # tri_annots는 후보, description_sim은 정렬용
        tri_annots[f"description_sim_{i}"] = trigram
        description_sim = description_sim + trigram
        location_score = location_score + Case(
            When(**{f"location_match_{i}": True}, then=Value(LOCATION_MATCH_SCORE)),
            default=Value(0.0),
            output_field=FloatField(),
        )

    qs = (
        Post.objects.annotate(**tri_annots, **location_annots)
        .annotate(
            title_score=title_score,
            hashtag_score=hashtag_score,
            description_score=description_sim,
            location_score=location_score,
        )
        .annotate(
            score=F("title_score")
            + F("hashtag_score")
            + F("description_score")
            + F("location_score"),
        )
        .filter(flt)
        .distinct()
        .order_by("-score", "-id")
    )

    result = list(qs[:300])
    cutted_ids = [p.id for p in result[:200]]

    cache.set(key, cutted_ids, SEARCH_TTL)
    return cutted_ids


def _search_key(tokens: list[Any]) -> str:
    norm = " ".join(sorted(t.lower() for t in tokens))
    return f"search:{norm}"
