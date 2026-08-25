from django.db import IntegrityError, transaction
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

        # exists() 사전 확인은 동시 요청(더블탭)에서 둘 다 통과할 수 있어
        # unique(post, user) 제약의 IntegrityError를 409로 변환하는 방식으로 대체.
        # 생성과 카운터 증가를 한 트랜잭션으로 묶어 부분 반영을 방지한다.
        try:
            with transaction.atomic():
                PostLike.objects.create(post=post, user=user)
                Post.objects.filter(id=post_id).update(like_count=F("like_count") + 1)
        except IntegrityError:
            raise ConflictException({"field_name": ["like"]})

        post.refresh_from_db()
        return post

    def unlike_post(self, post_id: str, user: User) -> Post:
        """게시글 좋아요 취소 서비스 로직"""
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("해당 게시글을 찾을 수 없습니다.")

        # 삭제된 행이 있을 때만 카운터를 감소시킨다.
        # 좋아요하지 않은 상태의 취소 요청(반복 호출·경합)이 무조건 -1을 실행하면
        # 임의 게시글의 like_count를 소거할 수 있고, 0에서는 PositiveIntegerField의
        # DB CHECK 위반(500)이 난다. 북마크 서비스와 동일한 멱등 삭제 계약.
        # 삭제+감소를 atomic으로 묶어 like_post·delete_comment와 대칭을 유지한다
        # (삭제 커밋 후 감소 실패 시 영구 over-count 방지).
        with transaction.atomic():
            deleted, _ = PostLike.objects.filter(post=post, user=user).delete()
            if deleted:
                Post.objects.filter(id=post_id).update(like_count=F("like_count") - 1)

        post.refresh_from_db()
        return post
