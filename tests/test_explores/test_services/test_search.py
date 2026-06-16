from unittest.mock import patch
from urllib.parse import urlencode

from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor

# ↓ 실제 모듈 경로로 수정하세요 (feeds_for_search 가 있는 파일)
from apps.explores.services.search import (
    PAGE_LIMIT,
    SEARCH_TTL,
    _clean,
    _search,
    _search_key,
    build_next,
    feeds_for_search,
)
from apps.posts.models import Post
from apps.users.models import User
from tests.test_explores.utils import user_and_posts

LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


# ---------------------------------------------------------------------------
# 순수 함수 (DB/캐시 불필요)
# ---------------------------------------------------------------------------
class CleanTest(SimpleTestCase):
    def test_strips_jamo(self) -> None:
        # 단독 자모(ㅋ, ㅎ 등)만 제거, 완성형 음절은 보존
        self.assertEqual(_clean("ㅋㅋㅋ"), "")
        self.assertEqual(_clean("안녕ㅎ"), "안녕")
        self.assertEqual(_clean("강아지"), "강아지")  # 완성형은 그대로

    def test_strips_whitespace(self) -> None:
        self.assertEqual(_clean("  hello  "), "hello")

    def test_english_untouched(self) -> None:
        self.assertEqual(_clean("hello world"), "hello world")


class SearchKeyTest(SimpleTestCase):
    def test_order_independent(self) -> None:
        # 토큰 순서가 달라도 같은 키여야 캐시가 공유됨
        self.assertEqual(
            _search_key(["world", "hello"]),
            _search_key(["hello", "world"]),
        )

    def test_lowercased(self) -> None:
        self.assertEqual(_search_key(["Hello"]), _search_key(["hello"]))

    def test_prefix_and_format(self) -> None:
        self.assertEqual(_search_key(["World", "Hello"]), "search:hello world")


class BuildNextTest(SimpleTestCase):
    def test_basic(self) -> None:
        url = build_next("hello", "abc123", "https://x.com/explore")
        self.assertEqual(
            url, "https://x.com/explore?search=hello&cursor=abc123&page_size=10"
        )

    def test_korean_is_percent_encoded(self) -> None:
        url = build_next("강아지", "c1", "https://x.com/explore")
        expected_qs = urlencode(
            {"search": "강아지", "cursor": "c1", "page_size": PAGE_LIMIT}
        )
        self.assertEqual(url, f"https://x.com/explore?{expected_qs}")
        self.assertNotIn("강아지", url)  # 그대로 노출되면 안 됨


# ---------------------------------------------------------------------------
# _search (캐시 동작)
# ---------------------------------------------------------------------------
@override_settings(CACHES=LOCMEM)
class SearchTest(TestCase):
    user: User
    posts: list[Post]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user, cls.posts = user_and_posts()

    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def test_cache_hit_skips_query(self) -> None:
        tokens = ["cached"]
        cache.set(_search_key(tokens), ["id1", "id2"], SEARCH_TTL)
        with self.assertNumQueries(0):  # DB 안 타야 함
            result = _search(tokens)
        self.assertEqual(result, ["id1", "id2"])

    def test_empty_cached_is_treated_as_hit(self) -> None:
        # 빈 리스트도 'is not None' 이라 히트 -> 재쿼리 안 함
        tokens = ["nomatch"]
        cache.set(_search_key(tokens), [], SEARCH_TTL)
        with self.assertNumQueries(0):
            result = _search(tokens)
        self.assertEqual(result, [])

    def test_cache_miss_queries_and_caches(self) -> None:
        """캐시 미스 시 쿼리 후 결과를 캐시에 저장.
        주의: TrigramSimilarity 때문에 pg_trgm 확장이 필요.
        'function similarity does not exist' 에러가 나면
        마이그레이션에 TrigramExtension() 추가 필요."""
        p = Post.objects.create(user=self.user, title="zztrigram 제목", thumbnail="t.jpg")
        tokens = ["zztrigram"]
        key = _search_key(tokens)
        self.assertIsNone(cache.get(key))

        result = _search(tokens)

        self.assertIn(p.id, result)  # title__icontains 매치
        self.assertEqual(cache.get(key), result)  # 저장됐는지


# ---------------------------------------------------------------------------
# feeds_for_search (메인 로직)
# ---------------------------------------------------------------------------
@override_settings(CACHES=LOCMEM)
class FeedsForSearchTest(TestCase):
    ids: list[str]
    posts: list[Post]
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user, cls.posts = user_and_posts()  # 25개 가정 (10/10/5)
        cls.ids = [p.id for p in cls.posts]

    def setUp(self) -> None:
        cache.clear()
        # 검색어를 정하고, 그 검색어가 만들 캐시 키에 순서를 직접 심는다.
        # -> _search 가 캐시 히트로 바로 반환하므로 페이지네이션이 결정적이 됨.
        self.search = "apple banana"
        self.tokens = _clean(self.search).split()
        cache.set(_search_key(self.tokens), self.ids, SEARCH_TTL)

        patcher = patch.object(
            s3_svc,
            "create_download_presigned_url",
            side_effect=lambda key: f"https://signed/{key}",
        )
        self.mock_s3 = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self) -> None:
        cache.clear()

    # --- 짧은/빈 검색어 차단 ---
    def test_empty_search_returns_empty(self) -> None:
        self.assertEqual(feeds_for_search("", None), ([], None, 0))

    def test_jamo_only_returns_empty(self) -> None:
        # 자모만 -> clean 후 "" -> 토큰 없음
        self.assertEqual(feeds_for_search("ㅋㅋㅋ", None), ([], None, 0))

    def test_single_short_token_returns_empty(self) -> None:
        # 단일 토큰 1글자 -> 차단
        self.assertEqual(feeds_for_search("a", None), ([], None, 0))

    def test_single_two_char_token_proceeds(self) -> None:
        # 경계: 2글자 단일 토큰은 통과해야 함 (< 2 조건)
        search = "ab"
        cache.set(_search_key(_clean(search).split()), self.ids, SEARCH_TTL)
        feeds, _, _ = feeds_for_search(search, None)
        self.assertEqual(len(feeds), PAGE_LIMIT)

    # --- 페이지네이션 ---
    def test_first_page(self) -> None:
        feeds, new_cursor, seed = feeds_for_search(self.search, None)
        self.assertEqual(len(feeds), PAGE_LIMIT)
        self.assertEqual({f.id for f in feeds}, set(self.ids[:PAGE_LIMIT]))
        self.assertEqual(new_cursor, encode_cursor(self.ids[PAGE_LIMIT - 1]))
        self.assertEqual(seed, 0)  # 이 구현은 seed 항상 0

    def test_second_page(self) -> None:
        cursor = self.ids[PAGE_LIMIT - 1]
        feeds, new_cursor, _ = feeds_for_search(self.search, cursor)
        self.assertEqual(
            {f.id for f in feeds}, set(self.ids[PAGE_LIMIT : PAGE_LIMIT * 2])
        )
        self.assertEqual(new_cursor, encode_cursor(self.ids[PAGE_LIMIT * 2 - 1]))

    def test_last_page_is_partial(self) -> None:
        feeds, _, _ = feeds_for_search(self.search, self.ids[19])
        self.assertEqual(len(feeds), 5)

    def test_cursor_at_end_returns_empty(self) -> None:
        feeds, new_cursor, seed = feeds_for_search(self.search, self.ids[-1])
        self.assertEqual(feeds, [])
        self.assertIsNone(new_cursor)
        self.assertEqual(seed, 0)

    def test_invalid_cursor_raises(self) -> None:
        with self.assertRaises(ValidationException):
            feeds_for_search(self.search, "INVALID_CURSOR")

    # --- 매핑 / S3 ---
    def test_search_result_mapping(self) -> None:
        feeds, _, _ = feeds_for_search(self.search, None)
        first = feeds[0]
        post = Post.objects.get(id=first.id)
        self.assertEqual(first.like_count, post.like_count)
        self.assertEqual(first.comment_count, post.comment_count)
        self.assertEqual(first.thumbnail, f"https://signed/{post.thumbnail}")

    def test_s3_called_per_item(self) -> None:
        feeds, _, _ = feeds_for_search(self.search, None)
        self.assertEqual(self.mock_s3.call_count, len(feeds))
