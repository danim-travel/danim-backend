from typing import Any, cast

from django.db.models import Count, Exists, OuterRef

from apps.follows.models.models import Follows
from apps.posts.models import Post, PostLike
from apps.posts.models.bookmark_model import BookMark
from apps.users.models import User


class PostMainListService:

    def get_main_list(self, user: User) -> Any:
        """팔로잉 피드 게시글 목록 조회 서비스 로직"""

        following_users = Follows.objects.filter(follower=user).values_list(
            "following", flat=True
        )

        queryset = cast(Any, Post.objects.filter(user__in=following_users))
        queryset = queryset.select_related("user").prefetch_related("spots__location")
        queryset = queryset.annotate(
            spot_count=Count("spots", distinct=True),
            comment_count=Count("comment", distinct=True),
            like_count=Count("post_likes", distinct=True),
            is_liked=Exists(PostLike.objects.filter(user=user, post_id=OuterRef("pk"))),
            is_bookmarked=Exists(
                BookMark.objects.filter(user=user, post_id=OuterRef("pk"))
            ),
        )
        return queryset
