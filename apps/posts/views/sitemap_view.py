from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.posts.schemas.sitemap_view_schema import sitemap_schema
from apps.posts.serializers.sitemap_serializer import SitemapSerializer
from apps.posts.services.sitemap_service import SitemapPagination, SitemapService


class SitemapView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sitemap"
    throttle_classes = [ScopedRateThrottle]
    service = SitemapService()

    @sitemap_schema
    def get(self, request: Request) -> Response:

        posts = self.service.get_sitemap_posts()
        paginator = SitemapPagination()
        page = paginator.paginate_queryset(posts, request)
        serializer = SitemapSerializer(page, many=True)

        return paginator.get_paginated_response(serializer.data)
