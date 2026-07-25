from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.posts.models import Post, PostLike
from apps.posts.services.post_like_service import PostLikeService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostLikeServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = PostLikeService()
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )

    def test_like_post(self) -> None:
        """게시글 좋아요 성공 테스트"""
        post = self.service.like_post(self.post.id, self.user)
        self.assertEqual(PostLike.objects.count(), 1)
        self.assertEqual(post.like_count, 1)

    def test_unlike_post(self) -> None:
        """게시글 좋아요 취소 성공 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        self.post.like_count = 1
        self.post.save()
        post = self.service.unlike_post(self.post.id, self.user)
        self.assertEqual(PostLike.objects.count(), 0)
        self.assertEqual(post.like_count, 0)

    def test_fail_like_post_not_found(self) -> None:
        """존재하지 않는 게시글 좋아요 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.like_post("nonexistent_id", self.user)

    def test_fail_like_post_conflict(self) -> None:
        """이미 좋아요한 게시글 좋아요 시 409 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        with self.assertRaises(ConflictException):
            self.service.like_post(self.post.id, self.user)

    def test_fail_unlike_post_not_found(self) -> None:
        """존재하지 않는 게시글 좋아요 취소 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.unlike_post("nonexistent_id", self.user)

    def test_unlike_post_without_like_keeps_count(self) -> None:
        """좋아요하지 않은 게시글 취소 시 카운터가 감소하지 않는다 (멱등)"""
        self.post.like_count = 3
        self.post.save()
        post = self.service.unlike_post(self.post.id, self.user)
        self.assertEqual(post.like_count, 3)  # 무조건 -1 회귀 방지
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 3)  # DB 영속값 검증

    def test_unlike_post_twice_decrements_once(self) -> None:
        """좋아요 1회 후 취소 2회 — 감소는 1회만, 0 미만(CHECK 위반 500) 방지"""
        self.service.like_post(self.post.id, self.user)
        self.service.unlike_post(self.post.id, self.user)
        post = self.service.unlike_post(self.post.id, self.user)  # 두 번째 취소
        self.assertEqual(post.like_count, 0)
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 0)

    def test_like_post_persists_count_in_db(self) -> None:
        """좋아요 후 응답값이 아닌 DB 영속 like_count를 검증"""
        self.service.like_post(self.post.id, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.like_count, 1)
        self.assertEqual(PostLike.objects.count(), 1)
