from django.utils import timezone

from apps.core.exceptions.exception import NotFoundException, ValidationException
from apps.directmessages.models import Conversation
from apps.users.models import User


def get_or_create_conversation(
    receiver_id: str, request_user: User
) -> tuple[Conversation, bool]:
    if receiver_id == request_user.id:
        raise ValidationException("자기 자신과는 대화방을 생성할 수 없습니다.")

    try:
        receiver = User.objects.get(id=receiver_id, is_active=True)
    except User.DoesNotExist:
        raise NotFoundException("존재하지 않는 유저입니다.")

    user1, user2 = sorted([request_user, receiver], key=lambda u: u.id)

    conversation, created = Conversation.objects.select_related(
        "user1", "user2"
    ).get_or_create(user1=user1, user2=user2)

    if not created:
        if conversation.user1_id == request_user.id and conversation.user1_left_at:
            conversation.user1_left_at = None
            conversation.user1_rejoin_at = timezone.now()  # type: ignore[attr-defined]
            conversation.save(update_fields=["user1_left_at", "user1_rejoin_at"])
            return conversation, True
        elif conversation.user2_id == request_user.id and conversation.user2_left_at:
            conversation.user2_left_at = None
            conversation.user2_rejoin_at = timezone.now()  # type: ignore[attr-defined]
            conversation.save(update_fields=["user2_left_at", "user2_rejoin_at"])
            return conversation, True

    return conversation, created
