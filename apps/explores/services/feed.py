import random
from datetime import datetime

from django.core.cache import cache
from django.utils import timezone

from apps.core.storage.s3 import s3_svc
from apps.explores.dtos import ExploreRes, TasteProfile
from apps.explores.services.order import main_order, new_order, sub_order
from apps.posts.models import Post
from apps.users.models import User, UserTaste

SLOT_LAYOUT = ["N", "M", "N", "M", "N", "S", "N", "M", "N", "M"]

NEW_COUNT = 5
MAIN_COUNT = 4
SUB_COUNT = 1
PAGE_SIZE = NEW_COUNT + MAIN_COUNT + SUB_COUNT

assert SLOT_LAYOUT.count("N") == NEW_COUNT
assert SLOT_LAYOUT.count("M") == MAIN_COUNT
assert SLOT_LAYOUT.count("S") == SUB_COUNT

CACHE_TTL = 60 * 30


def get_explore_feed(
    viewer: User,
    *,
    page: int = 0,
    seed: int | None = None,
    limit: int = PAGE_SIZE,
):
    """최종적으로 게시글 리스트를 반환하는 함수"""
    # 새로고침 등의 이유로 seed를 유저가 안 주면 seed 발급.
    # 클라가 문자열로 되돌려줄 수 있어 int를 씌움
    seed = random.randrange(1 << 30) if seed is None else int(seed)

    if viewer is not None and viewer.is_authenticated:
        profile = TasteProfile.from_taste(
            UserTaste.objects.filter(user=viewer.id).first()
        )
    else:
        profile = TasteProfile()

    feed = _feed(
        page=page,
        seed=seed,
        limit=limit,
        viewer=viewer,
        profile=profile,
    )
    return feed, seed


def _feed(
    *, page: int, seed: int, limit: int, viewer: User, profile: TasteProfile
) -> list[ExploreRes]:
    """post id 목록을 페이지 수만큼 잘라서 DB에서 post를 불러오는 함수."""

    now = timezone.now().replace(minute=0, second=0, microsecond=0)
    all_ids = _get_or_build_order(
        now,
        seed,
        viewer=viewer,
        profile=profile,
    )

    start = page * limit
    page_ids = all_ids[start : start + limit]
    if not page_ids:
        return []

    posts = Post.objects.select_related("user").filter(id__in=page_ids)
    order = {pid: idx for idx, pid in enumerate(page_ids)}
    ordered = sorted(posts, key=lambda p: order[p.id])
    return [
        ExploreRes(
            id=p.id,
            thumbnail=s3_svc.create_download_presigned_url(p.thumbnail),
            thumbnail_width=p.thumbnail_width,
            thumbnail_height=p.thumbnail_height,
            like_count=p.like_count,
            comment_count=p.comment_count,
        )
        for p in ordered
    ]


def _get_or_build_order(
    now: datetime, seed: int, *, viewer: User, profile: TasteProfile
) -> list[str]:
    """redis 에서 정렬된 id 리스트를 꺼내거나, 없으면 만들어 저장."""
    if viewer is not None and viewer.is_authenticated:
        uid = viewer.id
    else:
        uid = f"anon:{seed}"
    key = _explore_list_key(uid)
    cached = cache.get(key)
    if cached is not None and cached["seed"] == seed:
        return cached["ids"]

    feed_ids = _build_full_order(
        now,
        seed,
        profile=profile,
    )
    cache.set(key, {"seed": seed, "ids": feed_ids}, CACHE_TTL)
    return feed_ids


def _explore_list_key(uid):
    return f"feed:{uid}"


def _build_full_order(now: datetime, seed: int, *, profile: TasteProfile) -> list[str]:
    orders = {
        "M": main_order(now, seed, profile=profile),
        "N": new_order(now, seed, profile=profile),
        "S": sub_order(now, seed, profile=profile),
    }
    used = set()
    feed_ids = []
    cursor = {"M": 0, "N": 0, "S": 0}

    while True:
        added = False
        for slot in SLOT_LAYOUT:
            bucket = orders[slot]
            i = cursor[slot]
            if i < len(bucket):
                cursor[slot] = i + 1
                post = bucket[i]
                if post.id not in used:
                    used.add(post.id)
                    feed_ids.append(post.id)
                    added = True
        if not added:
            break

    return feed_ids
