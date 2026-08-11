from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import SitemapPagination, paginate
from apps.posts.schemas.sitemap_view_schema import sitemap_schema
from apps.posts.serializers.sitemap_serializer import SitemapSerializer
from apps.posts.services.sitemap_service import SitemapService


class SitemapView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "sitemap"
    service = SitemapService()

    @method_decorator(cache_page(60 * 30))
    @sitemap_schema
    def get(self, request: Request) -> Response:

        posts = self.service.get_sitemap_posts()

        return paginate(
            posts, request, SitemapSerializer, pagination_class=SitemapPagination
        )
