from django.db.models import Q

from apps.core.exceptions.exception import NotFoundException
from apps.directmessages.models import Conversation
from apps.users.models import User


def get_conversation_for_upload(conversation_id: str, request_user: User) -> None:
    """
    - DM 이미지 업로드 전 대화방 접근 권한 검증
    - 대화방 없거나 참여자가 아니거나 나간 상태면 404
    """
    try:
        Conversation.objects.get(
            Q(user1=request_user, user1_left_at__isnull=True)
            | Q(user2=request_user, user2_left_at__isnull=True),
            pk=conversation_id,
        )
    except Conversation.DoesNotExist:
        raise NotFoundException("대화방을 찾을 수 없습니다.")
