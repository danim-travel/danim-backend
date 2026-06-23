from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers

from apps.directmessages.serializers.message_list_serializer import MessageListSerializer


class MessageListWrapperSerializer(serializers.Serializer):
    next = serializers.CharField(allow_null=True)
    results = MessageListSerializer(many=True)


message_list_schema = extend_schema(
    parameters=[
        OpenApiParameter(name="cursor", description="커서 (다음 페이지)", required=False),
        OpenApiParameter(
            name="page_size",
            description="페이지 크기 (기본 10, 최대 100)",
            required=False,
        ),
    ],
    responses={
        200: MessageListWrapperSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="대화방을 찾을 수 없습니다."),
    },
    tags=["direct-messages"],
    summary="메시지 목록 조회",
)
