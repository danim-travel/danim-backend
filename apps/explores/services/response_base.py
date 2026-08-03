from urllib.parse import urlencode

from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.dtos import ExploreRes
from apps.posts.models import Post

PAGE_SIZE = 10


def build_next(
    url: str,
    *,
    search: str | None = None,
    region: str | None = None,
    cursor: str | None = None,
    page_size: int | None = None,
    seed: int | None = None,
) -> str:
    """다음 페이지 URL 생성.

    - 검색 path: search + cursor(post id, base62) + page_size
    - 지역 path: region + cursor(post id, base62) + page_size
    - 탐색 피드 path: cursor(페이지 번호) + page_size + seed
    None 인 파라미터는 쿼리스트링에서 제외한다.
    """
    if page_size is None:
        page_size = PAGE_SIZE

    query_params = {
        "search": search,
        "region": region,
        "cursor": cursor,
        "page_size": page_size,
        "seed": seed,
    }
    filtered_params = {k: v for k, v in query_params.items() if v is not None}
    return f"{url}?{urlencode(filtered_params)}"


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
