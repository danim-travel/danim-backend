from apps.core.exceptions.exception import (
    ConflictException,
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

    _, created = Follows.objects.get_or_create(
        following_id=target_user_id, follower_id=request_user.id
    )
    if not created:
        raise ConflictException("이미 팔로우한 유저입니다.")

    follow_count = Follows.objects.filter(following_id=target_user_id).count()

    result = {"follower_count": follow_count, "is_followed": True}

    create_notification(
        receiver_id=target_user_id,
        sender=request_user,
        noti_type="follow",
        target_id=target_user_id,
    )

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
