from datetime import date

from django.test import TestCase

from apps.posts.models import Post
from apps.posts.services.sitemap_service import SitemapService
from apps.users.models import User
from apps.users.models.models import LoginType


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

    def test_get_sitemap_posts_returns_all_posts(self) -> None:
        """전체 게시글이 후보 없이 그대로 조회된다"""
        post1 = Post.objects.create(user=self.user, title="t1")
        post2 = Post.objects.create(user=self.user, title="t2")

        queryset = self.service.get_sitemap_posts()

        self.assertEqual(set(queryset.values_list("id", flat=True)), {post1.id, post2.id})

    def test_ordered_by_id(self) -> None:
        """id(ULID) 오름차순으로 정렬된다 -> 응답 순서가 매 요청마다 흔들리지 않는다"""
        post1 = Post.objects.create(user=self.user, title="t1")
        post2 = Post.objects.create(user=self.user, title="t2")

        ids = list(self.service.get_sitemap_posts().values_list("id", flat=True))

        self.assertEqual(ids, sorted([post1.id, post2.id]))

    def test_empty_when_no_posts(self) -> None:
        """게시글이 없으면 빈 쿼리셋"""
        queryset = self.service.get_sitemap_posts()
        self.assertEqual(queryset.count(), 0)
