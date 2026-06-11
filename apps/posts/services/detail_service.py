from typing import Any, cast

from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post, PostLike
from apps.posts.models.bookmark_model import BookMark
from apps.users.models import User


class PostDetailService:

    def get_post_detail(self, post_id: str, user: User) -> Any:
        """게시글 상세 조회 서비스 로직"""

        if not Post.objects.filter(id=post_id).exists():
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        queryset = cast(Any, Post.objects.filter(id=post_id))
        queryset = queryset.select_related("user").prefetch_related(
            "spots__location", "spots__images"
        )
        queryset = queryset.annotate(
            like_count=Count("post_likes", distinct=True),
            comment_count=Count("comment", distinct=True),
            is_liked=(
                Exists(PostLike.objects.filter(user=user, post_id=OuterRef("pk")))
                if user.is_authenticated
                else Value(False, output_field=BooleanField())
            ),
            is_bookmarked=(
                Exists(BookMark.objects.filter(user=user, post_id=OuterRef("pk")))
                if user.is_authenticated
                else Value(False, output_field=BooleanField())
            ),
            is_owner=(
                Exists(Post.objects.filter(id=post_id, user=user))
                if user.is_authenticated
                else Value(False, output_field=BooleanField())
            ),
        )
        post = queryset.first()

        return post
