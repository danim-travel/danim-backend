from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers

from apps.directmessages.serializers.conversation_list_serializer import (
    ConversationListResponseSerializer,
)


class ConversationListWrapperSerializer(serializers.Serializer):
    results = ConversationListResponseSerializer(many=True)


conversation_list_schema = extend_schema(
    responses={
        200: ConversationListWrapperSerializer,
        401: OpenApiResponse(description="로그인이 필요합니다."),
    },
    tags=["direct-messages"],
    summary="대화 목록 조회",
)
