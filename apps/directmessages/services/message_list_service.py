from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound

from apps.directmessages.models import Conversation, Message
from apps.users.models import User


def get_message_list(conversation_id: str, request_user: User) -> QuerySet[Message]:
    try:
        Conversation.objects.get(
            Q(user1=request_user, user1_left_at__isnull=True)
            | Q(user2=request_user, user2_left_at__isnull=True),
            pk=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise NotFound("대화방을 찾을 수 없습니다.")

    return Message.objects.filter(conversation_id=conversation_id).select_related(
        "sender"
    )
