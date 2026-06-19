from urllib.parse import urlencode

PAGE_SIZE = 10


def build_next(
    url: str,
    *,
    search: str | None = None,
    cursor: str | None = None,
    page_size: int | None = None,
    seed: int | None = None,
) -> str:
    """다음 페이지 URL 생성.

    - 검색 path: search + cursor(post id, base62) + page_size
    - 탐색 피드 path: cursor(page 번호) + page_size + seed
    None 인 파라미터는 쿼리스트링에서 제외한다.
    """
    if page_size is None:
        page_size = PAGE_SIZE

    query_params = {
        "search": search,
        "cursor": cursor,
        "page_size": page_size,
        "seed": seed,
    }
    filtered_params = {k: v for k, v in query_params.items() if v is not None}
    return f"{url}?{urlencode(filtered_params)}"
