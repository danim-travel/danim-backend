from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.posts.models import Post
from apps.posts.models.bookmark_model import BookMark
from apps.posts.services.bookmark_service import BookmarkService
from apps.users.models import User
from apps.users.models.models import LoginType


class BookmarkServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = BookmarkService()
        self.user = User.objects.create(
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

    def test_create_bookmark(self) -> None:
        """북마크 추가 성공 테스트"""
        self.service.create_bookmark(post_id=self.post.id, request_user=self.user)
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 1
        )

    def test_fail_create_bookmark_not_found(self) -> None:
        """존재하지 않는 게시글 북마크 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.create_bookmark(post_id="nonexistent_id", request_user=self.user)

    def test_fail_create_bookmark_duplicate(self) -> None:
        """이미 북마크한 게시글 재북마크 시 409 테스트"""
        self.service.create_bookmark(post_id=self.post.id, request_user=self.user)
        with self.assertRaises(ConflictException):
            self.service.create_bookmark(post_id=self.post.id, request_user=self.user)
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 1
        )

    def test_delete_bookmark(self) -> None:
        """북마크 취소 성공 테스트"""
        BookMark.objects.create(post=self.post, user=self.user)
        self.user.bookmark_count = 1
        self.user.save()
        self.service.delete_bookmark(post_id=self.post.id, request_user=self.user)
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 0
        )

    def test_fail_delete_bookmark_not_found(self) -> None:
        """존재하지 않는 게시글 북마크 취소 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.delete_bookmark(post_id="nonexistent_id", request_user=self.user)

    def test_delete_bookmark_idempotent(self) -> None:
        """북마크하지 않은 상태에서 취소 시 에러 없이 통과(멱등) 테스트"""
        self.service.delete_bookmark(post_id=self.post.id, request_user=self.user)
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 0
        )
