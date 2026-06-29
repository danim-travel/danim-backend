from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from apps.posts.serializers.main_list_serializer import PostMainListSerializer

post_main_list_schema = extend_schema(
    tags=["posts"],
    summary="게시글 메인 리스트 조회",
    description="팔로잉한 유저의 게시글 목록을 최신순으로 조회합니다. (커서 페이지네이션)",
    parameters=[
        OpenApiParameter(
            name="cursor",
            location=OpenApiParameter.QUERY,
            required=False,
            type=str,
            description="다음 페이지 커서 (응답의 next에서 추출)",
        ),
        OpenApiParameter(
            name="page_size",
            location=OpenApiParameter.QUERY,
            required=False,
            type=int,
            description="페이지 크기 (기본 10, 최대 100)",
        ),
    ],
    responses={
        200: inline_serializer(
            name="PostMainListResponse",
            fields={
                "next": serializers.CharField(allow_null=True),
                "results": PostMainListSerializer(many=True),
            },
        ),
        401: OpenApiResponse(
            description="인증되지 않은 사용자입니다.",
            examples=[
                OpenApiExample(
                    "인증 실패",
                    value={"error_detail": "인증되지 않은 사용자입니다."},
                    response_only=True,
                )
            ],
        ),
    },
)
