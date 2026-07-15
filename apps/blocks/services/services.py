from django.db import transaction
from django.db.models import Q, QuerySet

from apps.blocks.models import Block
from apps.core.exceptions.exception import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from apps.follows.models.models import Follows
from apps.users.models import User


def is_blocked_between(user_id_a: str, user_id_b: str) -> bool:
    """두 유저 사이에 차단 관계가 있는가 (방향 무관).

    어느 쪽이 차단했든 팔로우·DM·댓글·알림 상호작용은 양방향으로 막는다.
    각 게이트(팔로우 생성·대화 생성·DM 전송·댓글 작성·알림 생성)가 이 함수
    하나를 공유한다 — 판단 기준이 흩어지지 않도록 여기서만 정의할 것.
    """
    return Block.objects.filter(
        Q(blocker_id=user_id_a, blocked_id=user_id_b)
        | Q(blocker_id=user_id_b, blocked_id=user_id_a)
    ).exists()


def block_user(request_user: User, target_user_id: str) -> None:
    """유저를 차단한다. 차단 시 기존 팔로우 관계는 양방향 모두 끊는다."""
    if str(target_user_id) == str(request_user.id):
        raise ValidationException("자기 자신은 차단할 수 없습니다.")
    if not User.objects.filter(id=target_user_id).exists():
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    with transaction.atomic():
        _, created = Block.objects.get_or_create(
            blocker_id=request_user.id, blocked_id=target_user_id
        )
        if not created:
            raise ConflictException("이미 차단한 유저입니다.")
        # 팔로우 절단은 차단 생성과 같은 트랜잭션 — 반쪽 상태(차단됐는데
        # 피드에 계속 뜨는 팔로우 잔존)를 만들지 않는다.
        Follows.objects.filter(
            Q(follower_id=request_user.id, following_id=target_user_id)
            | Q(follower_id=target_user_id, following_id=request_user.id)
        ).delete()


def unblock_user(request_user: User, target_user_id: str) -> None:
    """차단을 해제한다. 끊었던 팔로우는 복구하지 않는다(재팔로우는 본인 선택)."""
    deleted, _ = Block.objects.filter(
        blocker_id=request_user.id, blocked_id=target_user_id
    ).delete()
    if not deleted:
        raise NotFoundException("차단하지 않은 유저입니다.")


def get_block_list(user: User) -> QuerySet[Block]:
    return Block.objects.filter(blocker=user).select_related("blocked")
