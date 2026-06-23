from drf_spectacular.utils import OpenApiResponse, extend_schema

from apps.directmessages.serializers.conversation_create_serializer import (
    ConversationCreateSerializer,
    ConversationResponseSerializer,
)

conversation_create_schema = extend_schema(
    request=ConversationCreateSerializer,
    responses={
        200: ConversationResponseSerializer,
        201: ConversationResponseSerializer,
        400: OpenApiResponse(description="자기 자신과는 대화방을 생성할 수 없습니다."),
        401: OpenApiResponse(description="로그인이 필요합니다."),
        404: OpenApiResponse(description="존재하지 않는 유저입니다."),
    },
    tags=["direct-messages"],
    summary="대화방 생성",
)
