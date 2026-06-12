from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.directmessages.schemas.conversation_create_schema import (
    conversation_create_schema,
)
from apps.directmessages.serializers.conversation_create_serializer import (
    ConversationCreateSerializer,
    ConversationResponseSerializer,
)
from apps.directmessages.services.conversation_create_service import (
    get_or_create_conversation,
)


class ConversationView(APIView):
    permission_classes = [IsAuthenticated]

    @conversation_create_schema
    def post(self, request):
        serializer = ConversationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation, created = get_or_create_conversation(
            serializer.validated_data["receiver_id"], request.user
        )
        return Response(
            ConversationResponseSerializer(
                conversation, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
