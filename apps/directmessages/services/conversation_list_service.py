from typing import Any, cast

from django.db.models import F, OuterRef, Q, QuerySet, Subquery

from apps.directmessages.models import Conversation, Message
from apps.users.models import User


def get_conversation_list(request_user: User) -> QuerySet[Conversation]:
    """
    - 대화 목록 조회 서비스
    - last_message_at 내림차순 정렬 (메시지 없는 대화방은 맨 아래)
    - unread_count: 모델 필드(user1_unread_count / user2_unread_count) 직접 사용
    - last_message: Subquery로 N+1 방지
    """
    last_message: Any = Message.objects.filter(conversation=OuterRef("pk")).order_by(
        "-id"
    )

    base_qs: Any = (
        Conversation.objects.filter(Q(user1=request_user) | Q(user2=request_user))
        .exclude(
            Q(user1=request_user, user1_left_at__isnull=False)
            | Q(user2=request_user, user2_left_at__isnull=False)
        )
        .select_related("user1", "user2")
        .order_by(F("last_message_at").desc(nulls_last=True))
    )

    return cast(
        QuerySet[Conversation],
        base_qs.annotate(
            last_msg_content=Subquery(last_message.values("content")[:1]),
            last_msg_img_key=Subquery(last_message.values("img_key")[:1]),
            last_msg_created_at=Subquery(last_message.values("created_at")[:1]),
            last_msg_is_deleted=Subquery(last_message.values("is_deleted")[:1]),
        ),
    )
