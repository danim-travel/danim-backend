from dataclasses import dataclass


@dataclass(frozen=True)
class SearchResult:
    id: str
    thumbnail: str
    like_count: int
    comment_count: int
