from typing import Any

from django.core.cache import cache
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from apps.posts.models import Post
from apps.posts.redis import SitemapKey

SITEMAP_CACHE_TTL = 60 * 30
SITEMAP_MAX_URLS = 50000


class SitemapPagination(PageNumberPagination):
    page_size = 10000  # 최대 5만건 까지 가능 압축전 50Mb 까지 사용하가능

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
