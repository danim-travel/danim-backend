from datetime import date

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.posts.models import Post
from apps.posts.services.sitemap_service import SitemapService
from apps.users.models import User
from apps.users.models.models import LoginType

LOCMEM = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "auth": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


@override_settings(CACHES=LOCMEM)
class SitemapServiceTest(TestCase):

    service: SitemapService
    user: User

    def setUp(self) -> None:
        self.service = SitemapService()
        self.user = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        cache.clear()

    def test_get_sitemap_posts_returns_all_posts(self) -> None:
        """전체 게시글이 후보 없이 그대로 조회된다"""
        post1 = Post.objects.create(user=self.user, title="t1")
        post2 = Post.objects.create(user=self.user, title="t2")

        posts = self.service.get_sitemap_posts()

        self.assertEqual({p["id"] for p in posts}, {post1.id, post2.id})

    def test_ordered_by_id(self) -> None:
        """id(ULID) 오름차순으로 정렬된다 -> 응답 순서가 매 요청마다 흔들리지 않는다

        삽입 순서와 정렬 순서가 일치하면 order_by("id")를 지워도 통과해버리므로,
        큰 id를 먼저 삽입하고 작은 id를 나중에 삽입해 둘을 어긋나게 만든다.
        """
        post_large = Post.objects.create(
            id="01ZZZZZZZZZZZZZZZZZZZZZZZZ", user=self.user, title="t1"
        )
        post_small = Post.objects.create(
            id="01AAAAAAAAAAAAAAAAAAAAAAAA", user=self.user, title="t2"
        )

        with self.assertNumQueries(1):
            ids = [p["id"] for p in self.service.get_sitemap_posts()]

        self.assertEqual(ids, [post_small.id, post_large.id])

    def test_empty_when_no_posts(self) -> None:
        """게시글이 없으면 빈 리스트"""
        posts = self.service.get_sitemap_posts()
        self.assertEqual(posts, [])

    def test_second_call_hits_cache_not_db(self) -> None:
        """같은 요청 파라미터가 없어도, 고정 키 캐시라 두 번째 호출은 DB를 타지 않는다"""
        Post.objects.create(user=self.user, title="t1")

        self.service.get_sitemap_posts()  # 첫 호출 — 캐시 미스, DB 조회 + 캐싱

        with self.assertNumQueries(0):
            self.service.get_sitemap_posts()  # 두 번째 호출 — 캐시 히트
