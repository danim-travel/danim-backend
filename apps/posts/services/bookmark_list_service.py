from django.db.models import Exists,OuterRef

from apps.posts.models import PostLike
from apps.users.models import User
from apps.posts.models.bookmark_model import BookMark


class BookmarkListService:
    def get_bookmark_list(self, request_user: User):
        return (
            BookMark.objects.filter(user=request_user)
            .select_related("post", "post__user")
            .annotate(
                is_liked=Exists(
                    PostLike.objects.filter(
                        user=request_user, post_id=OuterRef("post_id")
                    )
                )
            )
            .order_by("-id")
        )

