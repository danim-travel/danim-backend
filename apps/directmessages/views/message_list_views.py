from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.directmessages.schemas.message_list_schema import message_list_schema
from apps.directmessages.serializers.message_list_serializer import MessageListSerializer
from apps.directmessages.services.message_list_service import get_message_list


class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    @message_list_schema
    def get(self, request, conversation_id):
        queryset = get_message_list(conversation_id, request.user)
        return paginate(queryset, request, MessageListSerializer)
