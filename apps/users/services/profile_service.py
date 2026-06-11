from django.db.models import Count, Exists, OuterRef

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.users.models import User


class ProfileService:

    def get_profile(self, user_id: str, request_user: User) -> User:
        user = (
            User.objects.annotate(
                follower=Count("following", distinct=True),
                following=Count("followers", distinct=True),
                posts_count=Count("posts", distinct=True),
                is_following=Exists(
                    Follows.objects.filter(
                        follower=request_user,
                        following=OuterRef("pk"),
                    )
                ),
            )
            .filter(id=user_id)
            .first()
        )
        if not user:
            raise NotFoundException("존재하지 않는 유저입니다.")
        return user
