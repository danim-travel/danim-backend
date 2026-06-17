from django.db.models import F

from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.posts.models import Post, PostLike
from apps.users.models import User


class PostLikeService:

    def like_post(self, post_id: str, user: User) -> Post:
        """게시글 좋아요 서비스 로직"""
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("해당 게시글을 찾을 수 없습니다.")

        if PostLike.objects.filter(post=post, user=user).exists():
            raise ConflictException({"field_name": ["like"]})

        PostLike.objects.create(post=post, user=user)
        Post.objects.filter(id=post_id).update(like_count=F("like_count") + 1)
        post.refresh_from_db()
        return post

    def unlike_post(self, post_id: str, user: User) -> Post:
        """게시글 좋아요 취소 서비스 로직"""
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("해당 게시글을 찾을 수 없습니다.")

        PostLike.objects.filter(post=post, user=user).delete()
        Post.objects.filter(id=post_id).update(like_count=F("like_count") - 1)
        post.refresh_from_db()
        return post
