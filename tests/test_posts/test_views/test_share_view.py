from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType


class PostShareViewTest(APITestCase):

    def setUp(self) -> None:
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
        self.url = reverse("posts:post_share", kwargs={"post_id": self.post.id})

    def test_get_share_url_view(self) -> None:
        """로그인한 유저의 게시글 공유 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("redirect_url", response.data)
        self.assertIn(self.post.id, response.data["redirect_url"])

    def test_get_share_url_view_unauthenticated(self) -> None:
        """비로그인 유저의 게시글 공유 성공 테스트"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("redirect_url", response.data)
        self.assertIn(self.post.id, response.data["redirect_url"])

    def test_fail_get_share_url_view_not_found(self) -> None:
        """존재하지 않는 게시글 공유 시 404 테스트"""
        url = reverse("posts:post_share", kwargs={"post_id": "nonexistent_id"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
