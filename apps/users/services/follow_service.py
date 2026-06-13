from django.db.models import Exists, OuterRef

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.users.models import User


class FollowService:

    def get_follower(self, user_id: str, request_user: User):
        if not User.objects.filter(id=user_id).exists():
            raise NotFoundException("존재하지 않는 유저입니다.")
        follower = (
            Follows.objects.filter(following=user_id)
            .select_related("follower")
            .annotate(
                is_following=Exists(
                    Follows.objects.filter(
                        follower=request_user, following=OuterRef("follower_id")
                    )
                )
            )
        )
        return follower
