from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema

from apps.posts.serializers.sitemap_serializer import SitemapSerializer

sitemap_schema = extend_schema(
    tags=["posts"],
    summary="SEO 사이트맵용 게시글 목록 조회",
    description="검색엔진 sitemap 생성을 위해 전체 게시글의 id/수정일자 목록을 반환합니다. 인증이 필요 없습니다.",
    responses={
        200: OpenApiResponse(
            response=SitemapSerializer(many=True),
            description="조회 성공",
            examples=[
                OpenApiExample(
                    "조회 성공",
                    value=[
                        {
                            "post_id": "01JWNZ8KQE4VXRM2P7HFGB3YDN",
                            "updated_at": "2026-07-04",
                        }
                    ],
                    response_only=True,
                )
            ],
        ),
    },
)
