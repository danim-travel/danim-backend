from django.db.models import Q
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.directmessages.models import Conversation, Message
from apps.users.models import User


def delete_message(conversation_id: str, message_id: str, request_user: User) -> None:
    try:
        Conversation.objects.get(
            Q(user1=request_user, user1_left_at__isnull=True)
            | Q(user2=request_user, user2_left_at__isnull=True),
            pk=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise NotFound("대화방을 찾을 수 없습니다.")

    try:
        message = Message.objects.get(pk=message_id, conversation_id=conversation_id)
    except Message.DoesNotExist:
        raise NotFound("메시지를 찾을 수 없습니다.")

    if message.sender_id != request_user.id:
        raise PermissionDenied("본인이 보낸 메시지만 삭제할 수 있습니다.")

    message.is_deleted = True
    message.save(update_fields=["is_deleted"])
