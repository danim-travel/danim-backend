from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post, PostLike
from apps.users.models import User
from apps.users.models.models import LoginType


class PostLikeViewTest(APITestCase):

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
        self.url = reverse("posts:post_like", kwargs={"post_id": self.post.id})

    def test_like_post_view(self) -> None:
        """로그인한 유저의 게시글 좋아요 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 1)

    def test_unlike_post_view(self) -> None:
        """로그인한 유저의 게시글 좋아요 취소 성공 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        self.post.like_count = 1
        self.post.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 0)

    def test_fail_like_post_view_unauthenticated(self) -> None:
        """비로그인 유저의 게시글 좋아요 시 401 테스트"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_like_post_view_not_found(self) -> None:
        """존재하지 않는 게시글 좋아요 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:post_like", kwargs={"post_id": "nonexistent_id"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_fail_like_post_view_conflict(self) -> None:
        """이미 좋아요한 게시글 좋아요 시 409 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_fail_unlike_post_view_unauthenticated(self) -> None:
        """비로그인 유저의 게시글 좋아요 취소 시 401 테스트"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_unlike_post_view_not_found(self) -> None:
        """존재하지 않는 게시글 좋아요 취소 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:post_like", kwargs={"post_id": "nonexistent_id"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
