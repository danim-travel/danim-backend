from datetime import date, datetime
from datetime import timezone as py_timezone

from django.test import TestCase
from django.utils import timezone as dj_timezone

from apps.posts.models import Post
from apps.posts.serializers.sitemap_serializer import SitemapSerializer
from apps.users.models import User
from apps.users.models.models import LoginType


class SitemapSerializerTest(TestCase):

    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )

    def test_fields(self) -> None:
        """post_id는 id에서, updated_at은 날짜(YYYY-MM-DD)만 직렬화된다

        DateTimeField가 TIME_ZONE(Asia/Seoul)으로 변환 후 포맷하므로, DB에 저장된
        UTC 원본이 아니라 KST로 변환된 날짜와 비교해야 한다(안 그러면 UTC 15:00~23:59에
        테스트가 도는 순간에만 실패하는 flaky 테스트가 된다).
        """
        post = Post.objects.create(user=self.user, title="test_title")

        data = SitemapSerializer(post).data

        self.assertEqual(data["post_id"], post.id)
        expected_date = dj_timezone.localtime(post.updated_at).strftime("%Y-%m-%d")
        self.assertEqual(data["updated_at"], expected_date)
        self.assertEqual(set(data.keys()), {"post_id", "updated_at"})

    def test_updated_at_converts_utc_to_kst_date(self) -> None:
        """UTC 15:00~23:59에 저장된 시각은 KST로 하루 넘어간 날짜로 직렬화된다"""
        post = Post.objects.create(user=self.user, title="test_title")
        Post.objects.filter(id=post.id).update(
            updated_at=datetime(2026, 8, 17, 23, 30, tzinfo=py_timezone.utc)
        )
        post.refresh_from_db()

        data = SitemapSerializer(post).data

        self.assertEqual(data["updated_at"], "2026-08-18")

    def test_updated_at_has_no_time_component(self) -> None:
        """updated_at은 DateTimeField이지만 시:분:초 없이 날짜만 나와야 한다"""
        post = Post.objects.create(user=self.user, title="test_title")

        data = SitemapSerializer(post).data

        self.assertNotIn("T", data["updated_at"])
        self.assertEqual(len(data["updated_at"]), len("YYYY-MM-DD"))

    def test_many(self) -> None:
        """many=True 로 여러 게시글 직렬화"""
        post1 = Post.objects.create(user=self.user, title="t1")
        post2 = Post.objects.create(user=self.user, title="t2")

        data = SitemapSerializer(
            Post.objects.filter(id__in=[post1.id, post2.id]), many=True
        ).data

        self.assertEqual({d["post_id"] for d in data}, {post1.id, post2.id})
