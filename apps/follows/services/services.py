from apps.blocks.services import is_blocked_between
from apps.core.exceptions.exception import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from apps.follows.models.models import Follows
from apps.notifications.utils import create_notification
from apps.users.models import User


def create_follow(target_user_id, request_user):
    if str(target_user_id) == str(request_user.id):
        raise ValidationException("자기 자신은 팔로우할 수 없습니다.")

    if not User.objects.filter(id=target_user_id).exists():
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    # 어느 쪽이 차단했든 팔로우 불가 (차단 시 기존 팔로우는 block_user가 절단)
    if is_blocked_between(request_user.id, target_user_id):
        raise ForbiddenException("차단 관계의 유저는 팔로우할 수 없습니다.")

    _, created = Follows.objects.get_or_create(
        following_id=target_user_id, follower_id=request_user.id
    )
    if not created:
        raise ConflictException("이미 팔로우한 유저입니다.")

    follow_count = Follows.objects.filter(following_id=target_user_id).count()

    result = {"follower_count": follow_count, "is_followed": True}

    return result


def delete_follow(target_user_id, request_user):
    if not User.objects.filter(id=target_user_id).exists():
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    deleted, _ = Follows.objects.filter(
        following_id=target_user_id, follower_id=request_user.id
    ).delete()
    if not deleted:
        raise NotFoundException("팔로우하지 않은 유저입니다.")

    follow_count = Follows.objects.filter(following_id=target_user_id).count()

    result = {"follower_count": follow_count, "is_followed": False}
    return result
