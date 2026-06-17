from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.posts.models.bookmark_model import BookMark
from apps.users.models import User
from apps.users.models.models import LoginType


class BookmarkListViewTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post1 = Post.objects.create(
            user=self.user, title="t1", description="d1", thumbnail="prod/p/1.jpg"
        )
        self.post2 = Post.objects.create(
            user=self.user, title="t2", description="d2", thumbnail="prod/p/2.jpg"
        )
        self.bm1 = BookMark.objects.create(user=self.user, post=self.post1)
        self.bm2 = BookMark.objects.create(user=self.user, post=self.post2)  # 최근
        self.url = reverse("posts:bookmark_list")

    def test_bookmark_list_view(self) -> None:
        """로그인 유저의 북마크 리스트 조회 성공"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("next", response.data)

    def test_fail_unauthenticated(self) -> None:
        """비로그인 시 401"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_response_fields(self) -> None:
        """응답 필드 구조 확인"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        item = response.data["results"][0]
        for field in [
            "post_id",
            "thumbnail",
            "description",
            "comment_count",
            "is_liked",
            "like_count",
        ]:
            self.assertIn(field, item)

    def test_ordered_recent_bookmark_first(self) -> None:
        """최근 북마크가 맨 앞"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        results = response.data["results"]
        self.assertEqual(results[0]["post_id"], self.post2.id)
        self.assertEqual(results[1]["post_id"], self.post1.id)

    def test_only_my_bookmarks(self) -> None:
        """다른 유저 북마크는 안 보인다"""
        other = User.objects.create(
            email="other@example.com",
            name="other",
            nickname="other_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        BookMark.objects.create(user=other, post=self.post1)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["results"]), 2)

    def test_empty_when_no_bookmark(self) -> None:
        """북마크 없는 유저는 빈 results"""
        empty_user = User.objects.create(
            email="empty@example.com",
            name="empty",
            nickname="empty_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.client.force_authenticate(user=empty_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])
