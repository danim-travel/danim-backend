from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from apps.posts.serializers.sitemap_serializer import SitemapSerializer

sitemap_schema = extend_schema(
    tags=["posts"],
    summary="SEO 사이트맵용 게시글 목록 조회",
    description=(
        "검색엔진 sitemap 생성을 위해 전체 게시글의 id/수정일자 목록을 반환합니다. "
        "인증이 필요 없습니다. sitemaps.org 프로토콜의 5만 건 상한을 지키기 위해 "
        "1만 건 단위 커서 페이지네이션으로 응답합니다."
    ),
    parameters=[
        OpenApiParameter(
            name="cursor",
            location=OpenApiParameter.QUERY,
            required=False,
            type=str,
            description="다음 페이지 커서 (응답의 next에서 추출)",
        ),
    ],
    responses={
        200: inline_serializer(
            name="SitemapListResponse",
            fields={
                "next": serializers.CharField(allow_null=True),
                "results": SitemapSerializer(many=True),
            },
        ),
    },
)
