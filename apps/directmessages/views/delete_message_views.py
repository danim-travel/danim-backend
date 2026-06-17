from typing import cast

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.directmessages.schemas.delete_message_schema import delete_message_schema
from apps.directmessages.serializers.delete_message_serializer import (
    DeleteMessageSerializer,
)
from apps.directmessages.services.delete_message_service import delete_message
from apps.users.models import User


class DeleteMessageView(APIView):
    permission_classes = [IsAuthenticated]

    @delete_message_schema
    def delete(self, request: Request, conversation_id: str, message_id: str) -> Response:
        serializer = DeleteMessageSerializer(
            data={"conversation_id": conversation_id, "message_id": message_id}
        )
        serializer.is_valid(raise_exception=True)
        validated_conversation_id = serializer.validated_data["conversation_id"]
        validated_message_id = serializer.validated_data["message_id"]
        delete_message(
            validated_conversation_id,
            validated_message_id,
            cast(User, request.user),
        )
        async_to_sync(get_channel_layer().group_send)(
            f"conversation_{validated_conversation_id}",
            {"type": "broadcast_message_deleted", "message_id": validated_message_id},
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
