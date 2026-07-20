import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ExploreRes:
    id: str
    thumbnail: str
    thumbnail_width: int | None
    thumbnail_height: int | None
    like_count: int
    comment_count: int


@dataclass
class TasteProfile:
    counts: dict | None = None
    version: str | None = None
    alpha: float = 0.0
    norm: float = 0.0

    @classmethod
    def from_taste(cls, taste):
        if taste is None:
            return cls()
        counts = taste.codeword_counts or None
        return cls(
            counts=counts,
            version=taste.codebook_version,
            alpha=taste.alpha,
            norm=_user_norm(counts),
        )

    @property
    def active(self) -> bool:
        return bool(self.counts) and self.alpha > 0


def _user_norm(taste_counts):
    """norm 계산"""
    if not taste_counts:
        return 0.0
    return math.sqrt(sum(float(v) * float(v) for v in taste_counts.values()))
