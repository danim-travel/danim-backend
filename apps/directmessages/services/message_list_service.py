from django.db.models import Q, QuerySet
from rest_framework.exceptions import NotFound

from apps.directmessages.models import Conversation, Message
from apps.users.models import User


def get_message_list(conversation_id: str, request_user: User) -> QuerySet[Message]:
    try:
        conversation = Conversation.objects.get(
            Q(user1=request_user) | Q(user2=request_user),
            pk=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise NotFound("대화방을 찾을 수 없습니다.")

    left_at = (
        conversation.user1_left_at
        if conversation.user1_id == request_user.id
        else conversation.user2_left_at
    )

    qs = Message.objects.filter(conversation=conversation).select_related("sender")

    if left_at:
        qs = qs.filter(created_at__lte=left_at)

    return qs
