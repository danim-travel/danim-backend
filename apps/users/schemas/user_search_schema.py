from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from apps.users.serializers.user_search_serializer import UserSearchResponseSerializer

user_search_schema = extend_schema(
    tags=["users"],
    summary="유저 검색",
    description=(
        "닉네임 또는 이름에 검색어가 포함된 유저를 조회합니다.\n\n"
        "- 커서 페이지네이션(기본 10개, `page_size`로 조절, 최대 100)\n"
        "- 다음 페이지는 응답의 `next` URL을 따라가면 됩니다(무한스크롤).\n"
        "- 검색어(`search`)는 필수이며, 비어 있으면 400을 반환합니다."
    ),
    parameters=[
        OpenApiParameter(
            name="search",
            location=OpenApiParameter.QUERY,
            required=True,
            type=str,
            description="검색어 (닉네임 또는 이름에 부분일치, 대소문자 무시)",
        ),
        OpenApiParameter(
            name="page_size",
            location=OpenApiParameter.QUERY,
            required=False,
            type=int,
            description="페이지당 개수 (기본 10, 최대 100)",
        ),
        OpenApiParameter(
            name="cursor",
            location=OpenApiParameter.QUERY,
            required=False,
            type=str,
            description="다음/이전 페이지 커서 (응답의 next/previous URL에 포함됨)",
        ),
    ],
    responses={
        200: inline_serializer(
            name="UserSearchPaginatedResponse",
            fields={
                "previous": serializers.CharField(allow_null=True),
                "next": serializers.CharField(allow_null=True),
                "results": UserSearchResponseSerializer(many=True),
            },
        ),
        400: OpenApiResponse(description="검색어는 필수입니다."),
        401: OpenApiResponse(description="자격 인증 데이터가 제공되지 않습니다."),
    },
)
