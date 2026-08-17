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
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIn("post_id", response.data["results"][0])
        self.assertIn("updated_at", response.data["results"][0])

    def test_response_is_paginated_wrapper(self) -> None:
        """5만 건 상한(sitemaps.org)을 지키기 위해 {"next","results"} 커서 페이지네이션으로 응답한다"""
        Post.objects.create(user=self.user, title="test_title")

        response = self.client.get(self.url)

        self.assertEqual(set(response.data.keys()), {"next", "results"})
        self.assertIsInstance(response.data["results"], list)

    def test_empty_when_no_posts(self) -> None:
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"next": None, "results": []})

    def test_throttle_not_bypassed_by_forwarded_for(self) -> None:
        """XFF 앞부분을 조작해도(nginx가 뒤에 진짜 IP를 붙이는 걸 흉내냄) 같은 클라이언트로 식별돼 429가 걸린다"""
        for i in range(12):
            response = self.client.get(
                self.url, HTTP_X_FORWARDED_FOR=f"10.0.0.{i},203.0.113.5"
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get(self.url, HTTP_X_FORWARDED_FOR="10.0.0.99,203.0.113.5")
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
