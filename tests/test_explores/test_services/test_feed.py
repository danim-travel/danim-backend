"""apps.explores.services.feed 테스트 (Django TestCase 기반).

─────────────────────────────────────────────────────────────────────
확인/조정이 필요한 가정 (assumptions)
  1) 테스트 대상 모듈 경로를 `apps.explores.services.feed` 로 가정했다.
     실제 경로가 다르면 아래 `feed as feed_mod` import 한 줄만 고치면 된다.
  2) 팩토리(make_shared_user, make_post)는 같은 tests 패키지의
     `factories` 모듈에 있다고 가정했다. 위치가 다르면 import 경로만 수정.
  3) main_order/new_order/sub_order 는 (now, seed, *, profile) 시그니처로
     `.id` 를 가진 post-like 객체의 list 를 반환한다고 가정했다.
     → _build_full_order 단위테스트는 .id 만 가진 _Stub 으로 통제한다.
─────────────────────────────────────────────────────────────────────

설계 메모
  - main/new/sub_order 를 mock 해서 M/N/S 버킷을 직접 통제 → 인터리빙·dedup·
    페이지 순서를 결정적으로 검증한다. (스코어링 자체는 여기 책임이 아님)
  - 모든 TestCase 는 _CacheTestCase 를 상속해 매 테스트 전후 cache 를 비운다.
"""

from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.explores.dtos import ExploreRes, TasteProfile
from apps.explores.services import feed as feed_mod
from apps.explores.services.feed import (
    PAGE_SIZE,
    _build_full_order,
    _explore_list_key,
    _feed,
    _get_or_build_order,
    get_explore_feed,
)

# ← (2) 팩토리 위치에 맞게 경로 조정
from tests.test_explores.utils import make_post, make_shared_user

NOW = timezone.now().replace(minute=0, second=0, microsecond=0)
SEED = 20260619


class _Stub:
    """_build_full_order 는 객체에서 .id 만 본다."""

    def __init__(self, _id):
        self.id = _id


def _patch_orders(*, m, n, s):
    """main/new/sub_order 를 고정 리스트 반환하도록 묶어서 패치하는 헬퍼."""
    return (
        patch.object(feed_mod, "main_order", return_value=m),
        patch.object(feed_mod, "new_order", return_value=n),
        patch.object(feed_mod, "sub_order", return_value=s),
    )


class _CacheTestCase(TestCase):
    """매 테스트 전후로 cache 를 비워 격리한다."""

    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()


# ───────────────────────── _explore_list_key ─────────────────────────
class ExploreListKeyTests(_CacheTestCase):
    def test_format(self):
        self.assertEqual(_explore_list_key(42), "feed:42")
        self.assertEqual(_explore_list_key("anon:7"), "feed:anon:7")


# ───────────────────────── _build_full_order ─────────────────────────
class BuildFullOrderTests(_CacheTestCase):
    def test_interleaves_by_slot_layout(self):
        """SLOT_LAYOUT(N M N M N S N M N M) 패턴대로 버킷을 인터리빙한다."""
        n = [_Stub(f"n{i}") for i in range(7)]
        m = [_Stub(f"m{i}") for i in range(5)]
        s = [_Stub(f"s{i}") for i in range(2)]

        p_m, p_n, p_s = _patch_orders(m=m, n=n, s=s)
        with p_m, p_n, p_s:
            ids = _build_full_order(NOW, SEED, profile=TasteProfile())

        # 버킷이 서로소이므로 전부 들어가고, 순서는 슬롯 레이아웃을 따른다.
        self.assertEqual(
            ids,
            [
                "n0",
                "m0",
                "n1",
                "m1",
                "n2",
                "s0",
                "n3",
                "m2",
                "n4",
                "m3",
                "n5",
                "m4",
                "n6",
                "s1",
            ],
        )
        self.assertEqual(len(ids), len(n) + len(m) + len(s))

    def test_dedupes_across_buckets(self):
        """여러 버킷에 같은 id 가 있어도 한 번만 담는다."""
        dup = _Stub("dup")
        n = [dup, _Stub("n1")]
        m = [dup, _Stub("m1")]
        s = [_Stub("s0")]

        p_m, p_n, p_s = _patch_orders(m=m, n=n, s=s)
        with p_m, p_n, p_s:
            ids = _build_full_order(NOW, SEED, profile=TasteProfile())

        self.assertEqual(ids.count("dup"), 1)
        self.assertEqual(set(ids), {"dup", "n1", "m1", "s0"})

    def test_empty_buckets_return_empty(self):
        p_m, p_n, p_s = _patch_orders(m=[], n=[], s=[])
        with p_m, p_n, p_s:
            ids = _build_full_order(NOW, SEED, profile=TasteProfile())
        self.assertEqual(ids, [])


# ───────────────────────── _get_or_build_order (cache) ─────────────────────────
class GetOrBuildOrderTests(_CacheTestCase):
    def test_builds_once_then_serves_cache(self):
        """같은 seed 로 두 번 호출하면 두 번째는 캐시 히트(재빌드 X)."""
        user = make_shared_user()

        with patch.object(feed_mod, "_build_full_order", return_value=["a", "b"]) as mb:
            first = _get_or_build_order(NOW, SEED, viewer=user, profile=TasteProfile())
            second = _get_or_build_order(NOW, SEED, viewer=user, profile=TasteProfile())

        self.assertEqual(first, ["a", "b"])
        self.assertEqual(second, ["a", "b"])
        self.assertEqual(mb.call_count, 1)

    def test_authenticated_uses_user_key(self):
        user = make_shared_user()

        with patch.object(feed_mod, "_build_full_order", return_value=["x"]):
            _get_or_build_order(NOW, SEED, viewer=user, profile=TasteProfile())

        self.assertEqual(cache.get(f"feed:{user.id}"), {"seed": SEED, "ids": ["x"]})

    def test_anon_key_includes_seed(self):
        """익명은 seed 로 키를 분리해 서로 덮어쓰지 않는다."""
        anon = AnonymousUser()

        with patch.object(feed_mod, "_build_full_order", return_value=["x"]):
            _get_or_build_order(NOW, SEED, viewer=anon, profile=TasteProfile())

        self.assertEqual(cache.get(f"feed:anon:{SEED}"), {"seed": SEED, "ids": ["x"]})
        # 다른 seed 는 다른 키 → 충돌하지 않음
        self.assertIsNone(cache.get(f"feed:anon:{SEED + 1}"))

    def test_rebuilds_when_seed_changes_for_same_user(self):
        """같은 유저(=같은 키)라도 캐시된 seed 가 다르면 재빌드한다."""
        user = make_shared_user()

        with patch.object(feed_mod, "_build_full_order", return_value=["a"]) as mb:
            _get_or_build_order(NOW, 111, viewer=user, profile=TasteProfile())
            _get_or_build_order(NOW, 222, viewer=user, profile=TasteProfile())

        self.assertEqual(mb.call_count, 2)


# ───────────────────────── _feed (pagination / ordering) ─────────────────────────
class FeedPaginationTests(_CacheTestCase):
    def test_paginates_and_preserves_id_order(self):
        """DB 가 임의 순서로 줘도 page_ids 순서를 그대로 복원한다."""
        user = make_shared_user()
        posts = [make_post(user) for _ in range(12)]
        # 생성/DB 순서와 일부러 다르게: 역순을 '정답 순서'로 사용
        ids = list(reversed([p.id for p in posts]))

        with patch.object(feed_mod, "_get_or_build_order", return_value=ids):
            page0 = _feed(page=0, seed=SEED, limit=5, viewer=user, profile=TasteProfile())
            page1 = _feed(page=1, seed=SEED, limit=5, viewer=user, profile=TasteProfile())
            page2 = _feed(page=2, seed=SEED, limit=5, viewer=user, profile=TasteProfile())

        self.assertEqual([p.id for p in page0], ids[0:5])
        self.assertEqual([p.id for p in page1], ids[5:10])
        self.assertEqual([p.id for p in page2], ids[10:12])

    def test_returns_empty_for_out_of_range_page(self):
        user = make_shared_user()
        posts = [make_post(user) for _ in range(3)]
        ids = [p.id for p in posts]

        with patch.object(feed_mod, "_get_or_build_order", return_value=ids):
            result = _feed(
                page=10, seed=SEED, limit=5, viewer=user, profile=TasteProfile()
            )

        self.assertEqual(result, [])


# ───────────────────────── get_explore_feed ─────────────────────────
class GetExploreFeedTests(_CacheTestCase):
    def test_returns_feed_and_seed(self):
        user = make_shared_user()
        posts = [make_post(user) for _ in range(PAGE_SIZE + 3)]
        ids = [p.id for p in posts]

        with (
            patch.object(feed_mod, "_get_or_build_order", return_value=ids),
            patch.object(TasteProfile, "from_taste", return_value=TasteProfile()),
        ):
            feed, seed = get_explore_feed(user, seed=42)

        self.assertEqual(seed, 42)
        self.assertEqual([p.id for p in feed], ids[:PAGE_SIZE])

    def test_coerces_string_seed_to_int(self):
        """클라가 seed 를 문자열로 돌려줘도 int 로 강제한다."""
        user = make_shared_user()

        with (
            patch.object(feed_mod, "_get_or_build_order", return_value=[]),
            patch.object(TasteProfile, "from_taste", return_value=TasteProfile()),
        ):
            _, seed = get_explore_feed(user, seed="123")

        self.assertEqual(seed, 123)
        self.assertIsInstance(seed, int)

    def test_generates_seed_when_none(self):
        user = make_shared_user()

        with (
            patch.object(feed_mod, "_get_or_build_order", return_value=[]),
            patch.object(TasteProfile, "from_taste", return_value=TasteProfile()),
        ):
            _, seed = get_explore_feed(user, seed=None)

        self.assertIsInstance(seed, int)
        self.assertGreaterEqual(seed, 0)
        self.assertLess(seed, 1 << 30)

    def test_anon_skips_taste_profile(self):
        """익명 viewer 는 UserTaste 조회 없이 빈 TasteProfile 을 쓴다."""
        anon = AnonymousUser()

        with (
            patch.object(TasteProfile, "from_taste") as mff,
            patch.object(feed_mod, "_feed", return_value=[]),
        ):
            get_explore_feed(anon, seed=1)

        mff.assert_not_called()

    def test_authenticated_builds_and_passes_profile(self):
        """인증 viewer 는 from_taste 로 만든 프로파일을 _feed 까지 흘려보낸다."""
        user = make_shared_user()
        sentinel = TasteProfile()

        with (
            patch.object(TasteProfile, "from_taste", return_value=sentinel) as mff,
            patch.object(feed_mod, "_feed", return_value=[]) as mfeed,
        ):
            get_explore_feed(user, seed=1)

        mff.assert_called_once()
        self.assertIs(mfeed.call_args.kwargs["profile"], sentinel)

    def test_returns_explore_res(self):
        user = make_shared_user()
        ids = [make_post(user).id for _ in range(3)]

        with (
            patch.object(feed_mod, "_get_or_build_order", return_value=ids),
            patch.object(TasteProfile, "from_taste", return_value=TasteProfile()),
            patch.object(
                feed_mod.s3_svc,
                "create_download_presigned_url",
                side_effect=lambda k: f"https://x/{k}",
            ),
        ):
            feed, _ = get_explore_feed(user, seed=1)

        self.assertTrue(feed)
        self.assertTrue(all(isinstance(item, ExploreRes) for item in feed))
