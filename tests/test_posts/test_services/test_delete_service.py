from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from apps.posts.models import Post
from apps.posts.services.delete_service import PostDeleteService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostDeleteServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = PostDeleteService()
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="other",
            nickname="other_nickname",
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

    def test_delete_post(self) -> None:
        """게시글 삭제 성공 테스트"""
        self.service.delete_post(self.post.id, self.user)
        self.assertEqual(Post.objects.count(), 0)

    def test_fail_delete_post_not_found(self) -> None:
        """존재하지 않는 게시글 삭제 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.delete_post("nonexistent_id", self.user)

    def test_fail_delete_post_not_owner(self) -> None:
        """본인 게시글이 아닐 시 403 테스트"""
        with self.assertRaises(ForbiddenException):
            self.service.delete_post(self.post.id, self.other_user)
