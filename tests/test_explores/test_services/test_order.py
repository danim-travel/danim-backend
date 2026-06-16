from unittest.mock import patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor

# ↓ call_posts / _get_posts_from_redis / PAGE_LIMIT 이 정의된 실제 모듈 경로로 수정하세요
from apps.explores.services.order import PAGE_LIMIT, _get_posts_from_redis, call_posts
from apps.posts.models import Post
from tests.test_explores.utils import user_and_posts

# 테스트 격리를 위해 로컬 메모리 캐시로 고정
LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CACHES=LOCMEM)
class GetPostsFromRedisTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, cls.posts = user_and_posts()
        cls.ids = [p.id for p in cls.posts]

    def tearDown(self):
        cache.clear()

    def test_cache_miss_populates_cache(self):
        self.assertIsNone(cache.get("order"))
        ids = _get_posts_from_redis()
        self.assertEqual(set(ids), set(self.ids))
        self.assertEqual(cache.get("order"), ids)

    def test_cache_hit_skips_db(self):
        cache.set("order", [999, 1000], 3600)
        with self.assertNumQueries(0):  # DB 안 타야 함
            ids = _get_posts_from_redis()
        self.assertEqual(ids, [999, 1000])


@override_settings(CACHES=LOCMEM)
class CallPostsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, cls.posts = user_and_posts()
        cls.ids = [p.id for p in cls.posts]

    def setUp(self):
        cache.clear()
        # 페이지네이션을 결정적으로 만들기 위해 캐시 순서를 직접 고정
        cache.set("order", self.ids, 3600)

        # 외부 S3 호출은 항상 목킹 (모듈 경로 몰라도 되도록 인스턴스 메서드를 패치)
        patcher = patch.object(
            s3_svc,
            "create_download_presigned_url",
            side_effect=lambda key: f"https://signed/{key}",
        )
        self.mock_s3 = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        cache.clear()

    def test_first_page(self):
        feeds, new_cursor, seed = call_posts(cursor=None)
        self.assertEqual(len(feeds), PAGE_LIMIT)
        self.assertEqual({f.id for f in feeds}, set(self.ids[:PAGE_LIMIT]))
        self.assertEqual(new_cursor, encode_cursor(self.ids[PAGE_LIMIT - 1]))
        self.assertIsInstance(seed, int)

    def test_second_page(self):
        cursor = self.ids[PAGE_LIMIT - 1]  # 첫 페이지 마지막 id (디코딩된 값 기준)
        feeds, new_cursor, _ = call_posts(cursor=cursor)
        self.assertEqual(
            {f.id for f in feeds}, set(self.ids[PAGE_LIMIT : PAGE_LIMIT * 2])
        )
        self.assertEqual(new_cursor, encode_cursor(self.ids[PAGE_LIMIT * 2 - 1]))

    def test_last_page_is_partial(self):
        cursor = self.ids[19]  # 20번째 id 다음부터 -> 5개 남음
        feeds, _, _ = call_posts(cursor=cursor)
        self.assertEqual(len(feeds), 5)

    def test_cursor_at_end_returns_empty(self):
        cursor = self.ids[-1]  # 마지막 id -> 다음 페이지 없음
        feeds, new_cursor, seed = call_posts(cursor=cursor)
        self.assertEqual(feeds, [])
        self.assertIsNone(new_cursor)
        self.assertIsInstance(seed, int)

    def test_invalid_cursor_raises(self):
        with self.assertRaises(ValidationException):
            call_posts(cursor=999_999)

    def test_search_result_mapping(self):
        feeds, _, _ = call_posts(cursor=None)
        first = feeds[0]
        post = Post.objects.get(id=first.id)  # 순서 보장 안 되므로 id로 매칭
        self.assertEqual(first.like_count, post.like_count)
        self.assertEqual(first.comment_count, post.comment_count)
        self.assertEqual(first.thumbnail, f"https://signed/{post.thumbnail}")

    def test_s3_called_per_item(self):
        feeds, _, _ = call_posts(cursor=None)
        self.assertEqual(self.mock_s3.call_count, len(feeds))

    # --- 아래 두 개는 위에서 언급한 '계약/버그' 고정용 ---

    def test_encoded_cursor_must_be_decoded_first(self):
        """call_posts는 디코딩된 raw id를 받는다.
        인코딩된 커서를 그대로 넣으면 index 실패 -> ValidationException.
        뷰 계층에서 decode 후 넘기는지 확인하는 의도."""
        _, new_cursor, _ = call_posts(cursor=None)  # base62 인코딩 문자열
        with self.assertRaises(ValidationException):
            call_posts(cursor=new_cursor)
