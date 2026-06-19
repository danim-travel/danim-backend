import math
import random

from django.test import TestCase
from django.utils import timezone

from apps.explores.services.order import (
    MAIN_CUT,
    PERSONALIZATION_BETA,
    SUB_CUT,
    _affinity_boosted,
    _main_score,
    _post_affinity,
    _post_embedding,
    _random_pool,
    _rookie_score,
    _sub_score,
    _weighted_order,
    main_order,
    new_order,
    sub_order,
)
from apps.posts.models import Post
from tests.test_explores.utils import (
    empty_profile,
    make_post,
    make_rec,
    make_shared_user,
    taste_profile,
)


def _ids(posts):
    return [p.id for p in posts]


# ── 개인화: 코사인 유사도 ──────────────────────────────────────────────────
class TestPostAffinity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_no_rec_returns_zero_and_does_not_raise(self):
        """rec(PostRec) 없는 글은 예외 없이 0.0 (개인화 스킵)."""
        post = make_post(self.user)
        profile = taste_profile({"1": 1.0})
        # _post_embedding 의 try/except 가 DoesNotExist 를 None 으로 흡수한다.
        self.assertIsNone(_post_embedding(post))
        self.assertEqual(_post_affinity(post, profile), 0.0)

    def test_inactive_profile_returns_zero(self):
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}])
        self.assertEqual(_post_affinity(post, empty_profile()), 0.0)

    def test_version_mismatch_returns_zero(self):
        """글 codebook_version 과 taste version 이 다르면 채점 스킵."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}], version="v2")
        profile = taste_profile({"1": 1.0}, version="v1")
        self.assertEqual(_post_affinity(post, profile), 0.0)

    def test_empty_codewords_returns_zero(self):
        post = make_post(self.user)
        make_rec(post, [])
        self.assertEqual(_post_affinity(post, taste_profile({"1": 1.0})), 0.0)

    def test_no_overlap_returns_zero(self):
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 3.0}])
        # 유저는 codeword 9 만 가지고 있어 겹침 없음 → dot 0
        self.assertEqual(_post_affinity(post, taste_profile({"9": 1.0})), 0.0)

    def test_identical_direction_is_one(self):
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 3.0}, {"codeword": 2, "weight": 4.0}])
        # u 와 p 방향이 같음 → cos = 1.0
        profile = taste_profile({"1": 3.0, "2": 4.0})
        self.assertAlmostEqual(_post_affinity(post, profile), 1.0, places=6)

    def test_partial_overlap_cosine(self):
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 3.0}, {"codeword": 2, "weight": 4.0}])
        # u={1:1}, ‖u‖=1, p=(3,4) ‖p‖=5, dot=3 → cos=3/(1*5)=0.6
        profile = taste_profile({"1": 1.0})
        self.assertAlmostEqual(_post_affinity(post, profile), 0.6, places=6)

    def test_missing_weight_defaults_zero(self):
        """weight 키 누락 시 0.0 으로 폴백(코드워드 키는 필수)."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1}])  # weight 없음
        # weight 0 이면 p_sq 0 → 0.0
        self.assertEqual(_post_affinity(post, taste_profile({"1": 1.0})), 0.0)


# ── 개인화: 부스트 배율 ────────────────────────────────────────────────────
class TestAffinityBoosted(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_inactive_profile_returns_base(self):
        post = make_post(self.user, like_count=10)
        base = lambda p: _rookie_score(p)
        score_fn = _affinity_boosted(base, alpha=1.0, profile=empty_profile())
        self.assertEqual(score_fn(post), base(post))

    def test_no_overlap_returns_base(self):
        post = make_post(self.user, like_count=10)
        make_rec(post, [{"codeword": 1, "weight": 1.0}])
        base = lambda p: _rookie_score(p)
        # 겹침 없는 유저 → cos 0 → base 그대로
        score_fn = _affinity_boosted(base, 1.0, taste_profile({"9": 1.0}))
        self.assertEqual(score_fn(post), base(post))

    def test_overlap_boosts_above_base(self):
        post = make_post(self.user, like_count=10)
        make_rec(post, [{"codeword": 1, "weight": 3.0}, {"codeword": 2, "weight": 4.0}])
        base = lambda p: _rookie_score(p)
        profile = taste_profile({"1": 3.0, "2": 4.0}, alpha=1.0)  # cos=1.0
        score_fn = _affinity_boosted(base, profile.alpha, profile)
        expected = base(post) * (math.exp(PERSONALIZATION_BETA * 1.0) ** 1.0)
        self.assertAlmostEqual(score_fn(post), expected, places=6)
        self.assertGreater(score_fn(post), base(post))


# ── 가중 랜덤 정렬 ─────────────────────────────────────────────────────────
class TestWeightedOrder(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()
        cls.posts = [make_post(cls.user, random_score=0.5) for _ in range(8)]

    def test_same_seed_is_deterministic(self):
        a = _weighted_order(self.posts, _rookie_score, seed="X")
        b = _weighted_order(self.posts, _rookie_score, seed="X")
        self.assertEqual(_ids(a), _ids(b))

    def test_seed_varies_ordering(self):
        """서로 다른 seed 는 (거의 항상) 다른 순서를 만든다."""
        orders = {
            tuple(_ids(_weighted_order(self.posts, _rookie_score, seed=str(s))))
            for s in range(5)
        }
        self.assertGreater(len(orders), 1)

    def test_cold_alpha_zero_ignores_score(self):
        """cold_alpha=0 이면 weight=1 로 고정 → 점수와 무관하게 동일 순서."""
        big = lambda p: 999.0
        zero = lambda p: 0.0
        a = _weighted_order(self.posts, big, seed="X", cold_alpha=0.0)
        b = _weighted_order(self.posts, zero, seed="X", cold_alpha=0.0)
        self.assertEqual(_ids(a), _ids(b))

    def test_zero_score_no_zero_division(self):
        """score 0 → (0+1)**alpha=1 이라 1/weight 0 나눗셈이 안 난다."""
        try:
            _weighted_order(self.posts, lambda p: 0.0, seed="X")
        except ZeroDivisionError:
            self.fail("score 0 에서 ZeroDivisionError 발생")

    def test_returns_permutation(self):
        out = _weighted_order(self.posts, _rookie_score, seed="X")
        self.assertEqual(set(_ids(out)), {p.id for p in self.posts})


# ── 랜덤 풀 추출 ───────────────────────────────────────────────────────────
class TestRandomPool(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_head_only_caps_at_pool_size(self):
        """모두 cut 이상이면 head 에서 pool_size 만큼만."""
        seed_key = "K"
        cut = random.Random(seed_key).random()
        for _ in range(6):
            make_post(self.user, random_score=min(cut + 0.1, 1.0))
        pool = _random_pool(Post.objects.all(), 4, seed_key)
        self.assertEqual(len(pool), 4)

    def test_tail_fallback_when_head_insufficient(self):
        """cut 이상 글이 모자라면 cut 미만(tail)에서 채운다."""
        seed_key = "K2"
        cut = random.Random(seed_key).random()
        # 전부 cut 미만 → head 비고 tail 로만 채워짐
        for _ in range(5):
            make_post(self.user, random_score=max(cut - 0.1, 0.0))
        pool = _random_pool(Post.objects.all(), 10, seed_key)
        # pool_size(10) > 글 수(5) → 전부 반환
        self.assertEqual(len(pool), 5)

    def test_personalize_select_related_no_n_plus_1(self):
        """personalize=True 시 select_related('rec') 로 rec 접근에 추가 쿼리 0."""
        profile = taste_profile({"1": 1.0})
        posts = []
        for _ in range(5):
            p = make_post(self.user)
            make_rec(p, [{"codeword": 1, "weight": 1.0}])
            posts.append(p)

        pool = _random_pool(Post.objects.all(), 10, "K3", personalize=True)
        with self.assertNumQueries(0):
            for p in pool:
                _post_affinity(p, profile)  # p.rec 접근(조인됨)


# ── new_order ──────────────────────────────────────────────────────────────
class TestNewOrder(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_only_includes_new_range(self):
        inside = make_post(self.user, days_ago=3)
        outside = make_post(self.user, days_ago=10)  # main 구간
        out = new_order(timezone.now(), seed=1, profile=empty_profile())
        ids = set(_ids(out))
        self.assertIn(inside.id, ids)
        self.assertNotIn(outside.id, ids)

    def test_dedup_and_permutation(self):
        """scored/shuffled 를 번갈아 합쳐도 중복 없이 풀 전체가 1번씩."""
        posts = [make_post(self.user, days_ago=2) for _ in range(6)]
        out = new_order(timezone.now(), seed=7, profile=empty_profile())
        ids = _ids(out)
        self.assertEqual(len(ids), len(set(ids)))  # 중복 없음
        self.assertEqual(set(ids), {p.id for p in posts})  # 풀 전체

    def test_empty_range_returns_empty(self):
        make_post(self.user, days_ago=40)  # new 범위 밖
        self.assertEqual(new_order(timezone.now(), seed=1, profile=empty_profile()), [])

    def test_personalize_on_off_same_set(self):
        """개인화는 순서에만 영향, 구성 글 집합은 동일."""
        posts = [make_post(self.user, days_ago=2) for _ in range(5)]
        for p in posts:
            make_rec(p, [{"codeword": 1, "weight": 1.0}])
        now = timezone.now()
        off = new_order(now, seed=3, profile=empty_profile())
        on = new_order(now, seed=3, profile=taste_profile({"1": 1.0}, alpha=1.0))
        self.assertEqual(set(_ids(off)), set(_ids(on)))


# ── main_order / sub_order ─────────────────────────────────────────────────
class TestMainSubOrder(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_main_range_filter(self):
        in_main = make_post(self.user, days_ago=15)
        too_new = make_post(self.user, days_ago=3)  # new 구간
        too_old = make_post(self.user, days_ago=45)  # sub 구간
        ids = set(_ids(main_order(timezone.now(), seed=1, profile=empty_profile())))
        self.assertIn(in_main.id, ids)
        self.assertNotIn(too_new.id, ids)
        self.assertNotIn(too_old.id, ids)

    def test_sub_range_filter(self):
        in_sub = make_post(self.user, days_ago=45)
        in_main = make_post(self.user, days_ago=15)
        too_old = make_post(self.user, days_ago=100)
        ids = set(_ids(sub_order(timezone.now(), seed=1, profile=empty_profile())))
        self.assertIn(in_sub.id, ids)
        self.assertNotIn(in_main.id, ids)
        self.assertNotIn(too_old.id, ids)

    def test_sub_cut_size(self):
        """sub 범위 글이 SUB_CUT 보다 많으면 정확히 SUB_CUT 개로 잘림."""
        for _ in range(SUB_CUT + 5):
            make_post(self.user, days_ago=45)
        out = sub_order(timezone.now(), seed=1, profile=empty_profile())
        self.assertEqual(len(out), SUB_CUT)

    def test_main_respects_cut_upper_bound(self):
        """공유된 [:CUT] 로직 검증(대량 생성 없이 상한만 확인)."""
        for _ in range(12):
            make_post(self.user, days_ago=15)
        out = main_order(timezone.now(), seed=1, profile=empty_profile())
        self.assertLessEqual(len(out), MAIN_CUT)
        self.assertEqual(len(out), 12)  # 12 < MAIN_CUT 이므로 전부 반환

    def test_empty_returns_empty(self):
        now = timezone.now()
        self.assertEqual(main_order(now, seed=1, profile=empty_profile()), [])
        self.assertEqual(sub_order(now, seed=1, profile=empty_profile()), [])

    def test_view_count_affects_sub_but_not_main(self):
        """_sub_score 는 view_count(log)를 반영, _main_score 는 무관."""
        now = timezone.now()
        p = make_post(self.user, days_ago=45, like_count=5, view_count=10)

        # 같은 객체에서 view_count 만 바꿔 confound(created_at 등) 제거
        p.view_count = 10
        sub_low = _sub_score(p, now)
        main_low = _main_score(p, now)
        p.view_count = 1000
        sub_high = _sub_score(p, now)
        main_high = _main_score(p, now)

        self.assertGreater(sub_high, sub_low)  # sub 는 view_count 반영
        self.assertEqual(main_high, main_low)  # main 은 view_count 무관
