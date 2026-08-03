from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.dtos import ExploreRes
from apps.posts.models import Post


def page_from_ids(
    ids: list[str], cursor: str | None, limit: int
) -> tuple[list[str], str | None]:
    """post id 커서 페이지네이션. 캐시 재빌드로 커서가 목록에서 사라지면 첫 페이지로 폴백."""
    if cursor:
        try:
            start = ids.index(cursor) + 1
        except ValueError:
            start = 0
    else:
        start = 0

    page_ids = ids[start : start + limit]
    if not page_ids:
        return [], None

    return page_ids, encode_cursor(page_ids[-1])


def build_feed(page_ids: list[str]) -> list[ExploreRes]:
    """page_ids 순서를 유지해 Post를 조회하고 ExploreRes로 조립."""
    queryset = Post.objects.filter(id__in=page_ids)
    rank = {pid: i for i, pid in enumerate(page_ids)}
    posts = sorted(queryset, key=lambda p: rank[p.id])
    return [
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
