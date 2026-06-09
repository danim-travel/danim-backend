from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.follows.models.models import Follows
from apps.users.models import User


def create_follow(target_user_id, request_user):
    if not User.objects.filter(id=target_user_id).exists():
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    _, is_already = Follows.objects.get_or_create(
        follower_id=target_user_id, following_id=request_user.id
    )

    if not is_already:
        raise ConflictException("이미 팔로잉 중입니다.")

    follow_count = Follows.objects.filter(follower_id=target_user_id).count()

    return follow_count
