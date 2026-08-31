from datetime import date
from unittest import mock

from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone as dj_timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.posts.services.sitemap_service import SitemapPagination
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
        post = Post.objects.create(user=self.user, title="test_title")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        result = response.data["results"][0]
        self.assertEqual(result["post_id"], post.id)
        self.assertEqual(
            result["updated_at"],
            dj_timezone.localtime(post.updated_at).strftime("%Y-%m-%d"),
        )

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

    @mock.patch.object(SitemapPagination, "page_size", 2)
    def test_pagination_covers_all_posts_exactly_once(self) -> None:
        """page_size를 줄여 여러 페이지에 걸친 순회가 누락·중복 없이 동작하는지 검증한다

        기본 page_size(1만)로는 테스트용 게시글 몇 건으로 절대 2페이지에 진입하지
        않아 next/다음 페이지 진입 경로가 한 번도 실행되지 않는다.
        """
        ids = {Post.objects.create(user=self.user, title=f"t{i}").id for i in range(5)}

        seen: list[str] = []
        url = self.url
        hops = 0
        while url:
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            seen += [result["post_id"] for result in response.data["results"]]
            url = response.data["next"]
            hops += 1
            self.assertLess(hops, 10)

        self.assertEqual(sorted(seen), sorted(ids))
        self.assertEqual(len(seen), len(set(seen)))
