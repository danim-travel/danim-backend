from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.users.models import User


def create_follow(target_user_id, request_user):
    if not User.objects.filter(id=target_user_id).exists():
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    _, created = Follows.objects.get_or_create(
        following_id=target_user_id, follower_id=request_user.id
    )

    follow_count = Follows.objects.filter(following_id=target_user_id).count()

    result = {"follower_count": follow_count, "is_followed": created}
    return result


def delete_follow(target_user_id, request_user):

    delete_follow_count, _ = Follows.objects.filter(
        following_id=target_user_id, follower_id=request_user.id
    ).delete()
    if not delete_follow_count:
        raise NotFoundException("해당 유저를 찾을 수 없습니다.")

    follow_count = Follows.objects.filter(following_id=target_user_id).count()

    result = {"follower_count": follow_count, "is_followed": False}
    return result
