import math
import random
from datetime import datetime, timedelta
from itertools import chain
from typing import Callable

from django.db.models import QuerySet

from apps.explores.dtos import TasteProfile
from apps.posts.models import Post, PostRec

#
SIGMOID_C = 120  # 시그모이드 중심 — 감쇠 배율이 0.5 되는 나이(일)
SIGMOID_S = 4  # 시그모이드 가파름 — 클수록 위로 볼록 + 중간 급락
COLD_ALPHA = 2.0  # ALPHA 클수록 인기순에 가깝고, 0이면 완전 균등 랜덤

#
NEW_MAX_DAYS = 7  # now-7d  < created_at <= now
MAIN_MAX_DAYS = 30  # now-30d < created_at <= now-7d
SUB_MAX_DAYS = 90  # now-90d <= created_at <= now-30d

#
NEW_POOL = 80  # 0d~7d 글 중 랜덤하게 80개

MAIN_POOL = 200  # 7d~30d 글 중 랜덤하게 200개를 가져온 뒤 정렬하여 100개로 cut
MAIN_CUT = 100

SUB_POOL = 50  # 30d~90d 글 중 랜덤하게 50개를 가져온 뒤 정렬하여 20개로 cut
SUB_CUT = 20

#
PERSONALIZATION_BETA = 2.5  # 개인화 점수에 반영.


# 인기도 점수 ===============================================
def _reaction(post: Post) -> float:
    return math.log1p(post.like_count + post.comment_count)


def _age_days(post: Post, now: datetime) -> float:
    return max(0.0, (now - post.created_at).total_seconds() / (60 * 60 * 24))


def _sigmoid_decay(
    age_days: float, center: int = SIGMOID_C, scale: int = SIGMOID_S
) -> float:
    """
    S자 모양 감쇠 곡선.
    center: 절반으로 감소하는 시간. center가 12일이라면 12일만에 절반으로 감소.
    scale: 클수록 그래프 곡선의 볼록함 정도가 올라감.
    """
    return 1.0 / (1.0 + (age_days / center) ** scale)


def _rookie_score(post: Post) -> float:
    """
    신규 구간의 인기글 추천용.
    한 게시글이 생성된지 7일까지가 사실상 신규글, 비인기글이 사람들에게 노출이 될 수 있는 마지노선.
    """
    return _reaction(post)


def _main_score(post: Post, now: datetime) -> float:
    """
    신규와 올드 구간 사이의 인기글 추천용.
    오래된 글일수록 reaction 점수가 높기 때문에 시간감쇠로 균형을 맞춤.
    """
    return _reaction(post) * _sigmoid_decay(_age_days(post, now))


def _sub_score(post: Post, now: datetime) -> float:
    """
    올드 구간의 인기글 추천용.
    이미 시간이 지난 글이라 감쇠는 약하게만 적용(center=120 기준 30~90일 구간).
    로그를 씌운 조회수를 점수에 반영.
    """
    return (
        _reaction(post)
        * math.log1p(post.view_count)
        * _sigmoid_decay(_age_days(post, now))
    )


# 개인화 점수 ==============================================
def _post_embedding(post: Post) -> PostRec | None:
    try:
        return post.rec
    except PostRec.DoesNotExist:
        return None


def _post_affinity(post: Post, profile: TasteProfile) -> float:
    """유저 취향 벡터와 게시글 벡터의 코사인 유사도를 반환하는 함수."""
    taste_counts = profile.counts
    u_norm = profile.norm
    taste_version = profile.version

    if not taste_counts or u_norm == 0.0:
        return 0.0
    emb = _post_embedding(post)
    if emb is None:
        return 0.0
    # 글 임베딩 버전과 taste 버전이 같을 때만 채점
    if taste_version is not None and emb.codebook_version != taste_version:
        return 0.0

    # cws = [{"codewords": int, "weight": float}, ...]
    cws = emb.codewords or None
    if not cws:
        return 0.0

    # 코사인 유사도: 내적(u, p) / (u 벡터 길이 * p 벡터 길이) (u: 유저 취향, p: 글 임베딩)
    dot = 0.0
    p_sq = 0.0
    for cw in cws:
        w = float(cw.get("weight", 0.0))
        p_sq += w * w
        uw = taste_counts.get(str(cw["codeword"]))
        if uw:
            dot += float(uw) * w
    if dot == 0.0 or p_sq == 0.0:
        return 0.0
    return dot / (u_norm * math.sqrt(p_sq))


def _affinity_boosted(
    base_score_fn: Callable[[Post], float], alpha: float, profile: TasteProfile
) -> Callable[[Post], float]:
    """
    인기도 점수 * 개인화 배율
    base * (e^(cos*α*β))
    """

    def score_fn(post):
        base = base_score_fn(post)
        if profile.norm == 0.0:
            return base
        cos = _post_affinity(post, profile)
        if cos <= 0.0:
            return base
        affinity = math.exp(PERSONALIZATION_BETA * cos)
        # alpha 는 0 이상 1 이하
        return base * (affinity**alpha)

    return score_fn


# 가중 랜덤 배열 ============================================================
def _weighted_order(
    posts: list[Post],
    score_fn: Callable[[Post], float],
    *,
    seed: str,
    cold_alpha: float = COLD_ALPHA,
) -> list[Post]:
    """최종 점수(인기도 or 인기도*개인화 or 균등랜덤)에 난수를 반영해 posts를 정렬하는 함수"""
    key_p = []
    for p in posts:
        # weight가 0인 걸 막기 위해 score + 1. cold_alpha는 인기도 점수의 반영도
        weight = (score_fn(p) + 1) ** cold_alpha
        # 시드와 posts가 같으면 항상 같은 피드가 나오도록. u는 0 이상 1 미만의 수
        u = random.Random(f"{seed}:{p.id}").random()
        key = u ** (1.0 / weight)
        key_p.append((key, p))
    # key가 큰 순으로 정렬
    key_p.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in key_p]


def _random_pool(
    base_qs: QuerySet[Post], pool_size: int, seed_key: str, *, personalize: bool = False
) -> list[Post]:
    """랜덤한 풀을 pool_size만큼 가져오는 함수."""
    cut = random.Random(seed_key).random()

    def _fetch(qs):
        if personalize:
            qs = qs.select_related("rec")
        return qs

    head = _fetch(base_qs.filter(random_score__gte=cut).order_by("random_score"))
    pool = list(head[:pool_size])

    # pool_size보다 모자라면 cut 미만에서 처음부터 채움
    if len(pool) < pool_size:
        tail = _fetch(base_qs.filter(random_score__lt=cut).order_by("random_score"))
        pool += list(tail[: pool_size - len(pool)])

    return pool


def new_order(now: datetime, seed: int, *, profile: TasteProfile) -> list[Post]:
    """
    now-7d ~ now 간의 posts를 최대 NEW_POOL개 랜덤 추출해서
    루키순/랜덤순으로 각각 정렬 후, 번갈아 합침(중복 제거).
    """
    hi = now
    lo = now - timedelta(days=NEW_MAX_DAYS)

    personalize = profile.active

    base_qs = Post.objects.select_related("user").filter(
        created_at__gt=lo, created_at__lte=hi
    )

    posts = _random_pool(
        base_qs,
        NEW_POOL,
        f"{seed}:new:cut",
        personalize=personalize,
    )

    # rookie 점수에 개인화 반영
    if personalize:
        scored_fn = _affinity_boosted(_rookie_score, profile.alpha, profile)
    else:
        scored_fn = _rookie_score
    scored = _weighted_order(posts, scored_fn, seed=f"{seed}:new:scored")

    # 균등 랜덤
    shuffled = _weighted_order(
        posts, lambda p: 0.0, seed=f"{seed}:new:rand", cold_alpha=0.0
    )

    merged, used = [], set()
    for p in chain.from_iterable(zip(scored, shuffled)):
        if p.id not in used:
            used.add(p.id)
            merged.append(p)
    return merged


def main_order(now: datetime, seed: int, *, profile: TasteProfile) -> list[Post]:
    """now-30d ~ now-7d 간의 posts를 정렬하는 함수"""
    personalize = profile.active

    hi = now - timedelta(days=NEW_MAX_DAYS)
    lo = now - timedelta(days=MAIN_MAX_DAYS)
    base_qs = Post.objects.only(
        "id", "created_at", "like_count", "comment_count", "view_count"
    ).filter(created_at__gt=lo, created_at__lte=hi)

    pool = _random_pool(
        base_qs,
        MAIN_POOL,
        f"{seed}:main:cut",
        personalize=personalize,
    )

    base_score_fn = lambda p: _main_score(p, now)
    score_fn = (
        _affinity_boosted(base_score_fn, profile.alpha, profile)
        if personalize
        else base_score_fn
    )
    return _weighted_order(pool, score_fn, seed=f"{seed}:main")[:MAIN_CUT]


def sub_order(now: datetime, seed: int, *, profile: TasteProfile) -> list[Post]:
    """now-90d ~ now-30d 의 posts를 정렬하는 함수."""
    personalize = profile.active

    hi = now - timedelta(days=MAIN_MAX_DAYS)
    lo = now - timedelta(days=SUB_MAX_DAYS)
    base_qs = Post.objects.only(
        "id", "created_at", "like_count", "comment_count", "view_count"
    ).filter(created_at__gte=lo, created_at__lte=hi)

    pool = _random_pool(
        base_qs,
        SUB_POOL,
        f"{seed}:sub:cut",
        personalize=personalize,
    )

    base_score_fn = lambda p: _sub_score(p, now)
    score_fn = (
        _affinity_boosted(base_score_fn, profile.alpha, profile)
        if personalize
        else base_score_fn
    )
    return _weighted_order(pool, score_fn, seed=f"{seed}:sub")[:SUB_CUT]
