from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.directmessages.schemas.message_list_schema import message_list_schema
from apps.directmessages.serializers.message_list_serializer import (
    MessageListPathSerializer,
    MessageListSerializer,
)
from apps.directmessages.services.message_list_service import get_message_list
from apps.users.models import User


class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    @message_list_schema
    def get(self, request: Request, conversation_id: str):
        serializer = MessageListPathSerializer(data={"conversation_id": conversation_id})
        serializer.is_valid(raise_exception=True)
        queryset = get_message_list(
            serializer.validated_data["conversation_id"], cast(User, request.user)
        )
        return paginate(queryset, request, MessageListSerializer)
