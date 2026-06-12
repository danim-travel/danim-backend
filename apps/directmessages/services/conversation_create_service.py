from apps.core.exceptions.exception import NotFoundException, ValidationException
from apps.directmessages.models import Conversation
from apps.users.models import User


def get_or_create_conversation(
    receiver_id: str, request_user: User
) -> tuple[Conversation, bool]:
    """
    - 대화방 생성 또는 기존 대화방 반환 서비스 로직
    - 자기 자신과의 대화방 생성 시도 시 400
    - receiver_id에 해당하는 유저가 없을 시 404
    - 기존 대화방 존재 시 (conversation, False) 반환
    - 새 대화방 생성 시 (conversation, True) 반환
    - user1_id < user2_id 강제로 항상 동일한 순서 보장 → 양방향 조회 불필요
    """

    if receiver_id == request_user.id:
        raise ValidationException("자기 자신과는 대화방을 생성할 수 없습니다.")

    try:
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        raise NotFoundException("존재하지 않는 유저입니다.")

    user1, user2 = sorted([request_user, receiver], key=lambda u: u.id)

    conversation, created = Conversation.objects.select_related(
        "user1", "user2"
    ).get_or_create(user1=user1, user2=user2)
    return conversation, created
