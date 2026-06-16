from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType


class PostDeleteViewTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create(
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
        self.url = reverse("posts:post_detail", kwargs={"post_id": self.post.id})

    def test_delete_post_view(self) -> None:
        """로그인한 유저의 게시글 삭제 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Post.objects.count(), 0)

    def test_fail_delete_post_view_unauthenticated(self) -> None:
        """비로그인 유저의 게시글 삭제 시 401 테스트"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_delete_post_view_not_owner(self) -> None:
        """본인 게시글이 아닐 시 403 테스트"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fail_delete_post_view_not_found(self) -> None:
        """존재하지 않는 게시글 삭제 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:post_detail", kwargs={"post_id": "nonexistent_id"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
