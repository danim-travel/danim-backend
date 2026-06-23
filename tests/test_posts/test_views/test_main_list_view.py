from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType


class PostMainListViewTest(APITestCase):

    user: User
    author: User
    url: str

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.author = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        Follows.objects.create(follower=self.user, following=self.author)
        Post.objects.create(
            user=self.author,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.url = reverse("posts:post_main_list")

    def test_get_main_list_view(self) -> None:
        """로그인한 유저의 메인 리스트 조회 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_fail_get_main_list_view_unauthenticated(self) -> None:
        """로그인 하지 않은 유저의 메인 리스트 조회 실패 테스트"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
