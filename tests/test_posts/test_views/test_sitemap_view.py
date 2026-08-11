from datetime import date

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType

LOCMEM = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "auth": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@override_settings(CACHES=LOCMEM)
class SitemapViewTest(APITestCase):

    user: User
    url: str

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.url = reverse("posts:post_sitemap")
        cache.clear()

    def test_get_sitemap_view_unauthenticated(self) -> None:
        """로그인 없이도 조회 가능 (SEO 크롤러 대상 공개 API)"""
        Post.objects.create(user=self.user, title="test_title")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn("post_id", response.data[0])
        self.assertIn("updated_at", response.data[0])

    def test_response_is_flat_array(self) -> None:
        """paginate 래퍼({"next","results"}) 없이 배열 그대로 응답"""
        Post.objects.create(user=self.user, title="test_title")

        response = self.client.get(self.url)

        self.assertIsInstance(response.data, list)

    def test_empty_when_no_posts(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_throttle_blocks_after_rate_limit(self) -> None:
        """sitemap 스코프 rate(12/hour)를 넘기면 13번째 요청부터 429가 반환된다"""
        for _ in range(12):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
