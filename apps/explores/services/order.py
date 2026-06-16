import random

from django.core.cache import cache

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.dtos import SearchResult
from apps.posts.models import Post

SEARCH_TTL = 60 * 60 * 24
PAGE_LIMIT = 10


def _get_posts_from_redis():
    cached = cache.get("order")
    if cached:
        return cached

    posts = Post.objects.all()[:100]
    ids = [p.id for p in posts]
    cache.set("order", ids, SEARCH_TTL)
    return ids


def call_posts(cursor):
    seed = random.randrange(1 << 30)
    ids = _get_posts_from_redis()

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
    posts = Post.objects.filter(id__in=page_ids)

    feeds = []
    for p in posts:
        feeds.append(
            SearchResult(
                id=p.id,
                thumbnail=s3_svc.create_download_presigned_url(p.thumbnail),
                like_count=p.like_count,
                comment_count=p.comment_count,
            )
        )
    return feeds, new_cursor, seed
