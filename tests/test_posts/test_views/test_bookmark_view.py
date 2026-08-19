from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.posts.models.bookmark_model import BookMark
from apps.users.models import User
from apps.users.models.models import LoginType


class BookmarkViewTest(APITestCase):

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
        self.url = reverse("posts:bookmark", kwargs={"post_id": self.post.id})

    def test_create_bookmark_view(self) -> None:
        """로그인한 유저의 북마크 추가 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["is_bookmarked"])
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 1
        )

    def test_fail_create_bookmark_view_unauthenticated(self) -> None:
        """비로그인 유저의 북마크 추가 시 401 테스트"""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_create_bookmark_view_not_found(self) -> None:
        """존재하지 않는 게시글 북마크 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:bookmark", kwargs={"post_id": "nonexistent_id"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_fail_create_bookmark_view_duplicate(self) -> None:
        """이미 북마크한 게시글 재북마크 시 409 테스트"""
        BookMark.objects.create(post=self.post, user=self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_delete_bookmark_view(self) -> None:
        """로그인한 유저의 북마크 취소 성공 테스트"""
        BookMark.objects.create(post=self.post, user=self.user)
        self.user.bookmark_count = 1
        self.user.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_bookmarked"])
        self.assertEqual(
            BookMark.objects.filter(post=self.post, user=self.user).count(), 0
        )

    def test_fail_delete_bookmark_view_unauthenticated(self) -> None:
        """비로그인 유저의 북마크 취소 시 401 테스트"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_delete_bookmark_view_not_found(self) -> None:
        """존재하지 않는 게시글 북마크 취소 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:bookmark", kwargs={"post_id": "nonexistent_id"})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
