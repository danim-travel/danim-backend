from datetime import date

from django.test import RequestFactory, TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post
from apps.posts.services.share_service import PostShareService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostShareServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = PostShareService()
        self.factory = RequestFactory()
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

    def test_get_share_url(self) -> None:
        """게시글 공유 URL 반환 성공 테스트"""
        request = self.factory.get("/")
        url = self.service.get_share_url(self.post.id, request)
        self.assertIn(self.post.id, url)
        self.assertIn("/api/v1/posts/", url)

    def test_fail_get_share_url_not_found(self) -> None:
        """존재하지 않는 게시글 공유 시 404 테스트"""
        request = self.factory.get("/")
        with self.assertRaises(NotFoundException):
            self.service.get_share_url("nonexistent_id", request)
