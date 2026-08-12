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

    def get_sitemap_posts(self):
        cache_key = cache.get(SitemapKey.key())
        if cache_key is not None:
            return cache_key
        posts = list(
            Post.objects.order_by("id").values("id", "updated_at")[:SITEMAP_MAX_URLS]
        )
        cache.set(SitemapKey.key(), posts, SITEMAP_CACHE_TTL)
        return posts
