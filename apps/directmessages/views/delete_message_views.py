from typing import cast

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
        delete_message(
            serializer.validated_data["conversation_id"],
            serializer.validated_data["message_id"],
            cast(User, request.user),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
