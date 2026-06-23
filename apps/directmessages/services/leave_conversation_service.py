from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.directmessages.models import Conversation
from apps.users.models import User


def leave_conversation(conversation_id: str, request_user: User) -> None:
    try:
        conversation = Conversation.objects.get(
            Q(user1=request_user, user1_left_at__isnull=True)
            | Q(user2=request_user, user2_left_at__isnull=True),
            pk=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise NotFound("대화방을 찾을 수 없습니다.")

    if conversation.user1_id == request_user.id:
        conversation.user1_left_at = timezone.now()
        conversation.save(update_fields=["user1_left_at"])
    else:
        conversation.user2_left_at = timezone.now()
        conversation.save(update_fields=["user2_left_at"])
