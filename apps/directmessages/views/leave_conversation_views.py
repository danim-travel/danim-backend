from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.directmessages.schemas.leave_conversation_schema import (
    leave_conversation_schema,
)
from apps.directmessages.serializers.leave_conversation_serializer import (
    LeaveConversationSerializer,
)
from apps.directmessages.services.leave_conversation_service import leave_conversation
from apps.users.models import User


class LeaveConversationView(APIView):
    permission_classes = [IsAuthenticated]

    @leave_conversation_schema
    def delete(self, request: Request, conversation_id: str) -> Response:
        serializer = LeaveConversationSerializer(
            data={"conversation_id": conversation_id}
        )
        serializer.is_valid(raise_exception=True)
        leave_conversation(
            serializer.validated_data["conversation_id"], cast(User, request.user)
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
