from typing import Any

from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.posts.models import Post
from apps.posts.redis import SitemapKey

SITEMAP_CACHE_TTL = 60 * 30
# sitemaps.org 0.9 상한(파일당 URL 5만 건 / 50MB) — 이 값을 넘는 게시글은
# 캐시에 아예 담기지 않는다. 청크 분할(sitemap index)은 별도 프론트 계약
# 변경이 필요해 아직 미도입.
SITEMAP_MAX_URLS = 50000
# 한 응답(페이지)당 건수. config/settings/base.py의 DEFAULT_THROTTLE_RATES
# ["sitemap"] 값(12/hour)이 이 값을 전제로 산출됐다 — 여기를 바꾸면 그 rate도
# 같이 재계산해야 전체 목록을 1시간 안에 순회할 수 있다는 보장이 깨지지 않는다.
SITEMAP_PAGE_SIZE = 10_000


class SitemapPagination(PageNumberPagination):
    page_size = SITEMAP_PAGE_SIZE

    def get_paginated_response(self, data):
        return Response({"next": self.get_next_link(), "results": data})


class SitemapService:

    def get_sitemap_posts(self) -> list[Any]:
        cache_key = cache.get(SitemapKey.key())
        if cache_key is not None:
            return cache_key
        # 발행/비공개 상태 필터 없음 — 의도된 것이다. PostDetailView 등 다른 조회
        # API들도 현재 동일하게 user.is_active/게시글 공개 여부를 걸러내지 않는다.
        # 비공개·임시저장·정지 개념이 생기면 이 쿼리도 반드시 같이 갱신해야 한다.
        posts = list(
            Post.objects.order_by("id").values("id", "updated_at")[:SITEMAP_MAX_URLS]
        )
        cache.set(SitemapKey.key(), posts, SITEMAP_CACHE_TTL)
        return posts
