from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from apps.comments.models import Comment
from apps.explores.services.taste import (
    ALPHA_FULL,
    TASTE_WEIGHTS,
    _last_active_at,
    _sigmoid_decay,
    build_codeword_counts,
    personalization_alpha,
)
from apps.posts.models import BookMark, PostClick, PostLike
from apps.users.models import LoginType, User
from tests.test_explores.utils import make_post, make_rec, make_shared_user


# ── 상호작용 생성 헬퍼 ──────────────────────────────────────────────────────
# make_post 와 동일한 패턴: auto_now_add 인 created_at 을 update 로 덮어쓴다.
def _set_created_at(model, obj, days_ago):
    if days_ago:
        ts = timezone.now() - timedelta(days=days_ago)
        model.objects.filter(pk=obj.pk).update(created_at=ts)
        obj.refresh_from_db()
    return obj


def _like(user, post, days_ago=0):
    return _set_created_at(
        PostLike, PostLike.objects.create(user=user, post=post), days_ago
    )


def _click(user, post, days_ago=0):
    return _set_created_at(
        PostClick, PostClick.objects.create(user=user, post=post), days_ago
    )


def _bookmark(user, post, days_ago=0):
    return _set_created_at(
        BookMark, BookMark.objects.create(user=user, post=post), days_ago
    )


def _comment(user, post, days_ago=0):
    # NOTE: Comment 의 필수 필드(여기선 content 로 가정)는 실제 스키마에 맞춰 조정할 것.
    obj = Comment.objects.create(user=user, post=post, content="c")
    return _set_created_at(Comment, obj, days_ago)


def _other_user():
    """격리 테스트용 두 번째 유저(unique 필드는 shared user 와 겹치지 않게)."""
    return User.objects.create(
        email="other@example.com",
        name="other",
        nickname="othernick",
        password="Password@123",
        phone_number="01099998888",
        birth_day=date(1980, 1, 1),
        is_email_verified=True,
        is_phone_verified=True,
        is_active=True,
        login_type=LoginType.EMAIL,
    )


# ── 시간감쇠 함수 ──────────────────────────────────────────────────────────
class TestSigmoidDecay(TestCase):
    def test_zero_age_is_one(self):
        """age=0 이면 감쇠 없음 → 1.0."""
        self.assertEqual(_sigmoid_decay(0), 1.0)
        self.assertEqual(_sigmoid_decay(0, center=60, scale=2), 1.0)

    def test_at_center_is_half(self):
        """age=center 이면 정확히 절반(0.5)."""
        self.assertAlmostEqual(_sigmoid_decay(7), 0.5)  # 기본 center=7
        self.assertAlmostEqual(_sigmoid_decay(90, center=90, scale=3), 0.5)
        self.assertAlmostEqual(_sigmoid_decay(60, center=60, scale=2), 0.5)

    def test_monotonic_decreasing(self):
        """age 가 커질수록 값은 단조감소."""
        vals = [_sigmoid_decay(d, center=30, scale=2) for d in range(0, 300, 15)]
        for a, b in zip(vals, vals[1:]):
            self.assertGreater(a, b)

    def test_bounded_between_zero_and_one(self):
        for d in (0, 1, 30, 90, 365, 100_000):
            v = _sigmoid_decay(d, center=90, scale=3)
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_larger_scale_decays_faster_past_center(self):
        """center 밖(age>center)에서는 scale 이 클수록 더 가파르게 감쇠."""
        soft = _sigmoid_decay(120, center=60, scale=2)
        hard = _sigmoid_decay(120, center=60, scale=4)
        self.assertLess(hard, soft)


# ── 최근 활동일 ────────────────────────────────────────────────────────────
class TestLastActiveAt(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_no_interactions_returns_none(self):
        self.assertIsNone(_last_active_at(self.user))

    def test_single_interaction_returns_its_time(self):
        post = make_post(self.user)
        like = _like(self.user, post, days_ago=5)
        self.assertEqual(_last_active_at(self.user), like.created_at)

    def test_returns_latest_across_models(self):
        """여러 모델에 걸쳐 가장 최근 created_at 을 반환."""
        p1, p2, p3 = (make_post(self.user) for _ in range(3))
        _like(self.user, p1, days_ago=10)
        _click(self.user, p2, days_ago=3)
        newest = _bookmark(self.user, p3, days_ago=1)  # 가장 최근
        self.assertEqual(_last_active_at(self.user), newest.created_at)

    def test_ignores_other_users(self):
        other = _other_user()
        post = make_post(self.user)
        _like(other, post)  # 다른 유저의 활동
        self.assertIsNone(_last_active_at(self.user))


# ── 개인화 alpha ───────────────────────────────────────────────────────────
class TestPersonalizationAlpha(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_no_interactions_returns_zero(self):
        """last_active 없음(콜드 스타터) → 0.0."""
        self.assertEqual(personalization_alpha(self.user), 0.0)

    def test_fresh_activity_in_unit_interval(self):
        post = make_post(self.user)
        _like(self.user, post)
        a = personalization_alpha(self.user)
        self.assertGreater(a, 0.0)
        self.assertLessEqual(a, 1.0)

    def test_exact_value_for_fresh_interactions(self):
        """좋아요1 + 북마크1(모두 now) → strength 2.0 → alpha 0.02, idle 감쇠 1.0."""
        p1, p2 = make_post(self.user), make_post(self.user)
        _like(self.user, p1)  # 0.8
        _bookmark(self.user, p2)  # 1.2
        self.assertAlmostEqual(personalization_alpha(self.user), 0.02, places=6)

    def test_bookmark_weighs_more_than_click(self):
        """동일 조건(now, 1건)에서 북마크가 클릭보다 큰 alpha 를 만든다."""
        other = _other_user()
        pa, pb = make_post(self.user), make_post(other)
        _bookmark(self.user, pa)
        _click(other, pb)
        a_book = personalization_alpha(self.user)
        a_click = personalization_alpha(other)
        self.assertAlmostEqual(a_book, TASTE_WEIGHTS["bookmark"] / ALPHA_FULL, places=6)
        self.assertAlmostEqual(a_click, TASTE_WEIGHTS["click"] / ALPHA_FULL, places=6)
        self.assertGreater(a_book, a_click)

    def test_idle_penalty_matches_formula(self):
        """오래된 마지막 활동일수록 idle 감쇠가 곱해져 줄어든다(공식 일치 검증)."""
        post = make_post(self.user)
        _like(self.user, post, days_ago=7)
        interaction_decay = _sigmoid_decay(7, center=90, scale=3)
        strength = interaction_decay * TASTE_WEIGHTS["like"]
        alpha = min(1.0, strength / ALPHA_FULL)
        expected = alpha * _sigmoid_decay(7, center=7, scale=5)  # idle 7일 → 0.5
        self.assertAlmostEqual(personalization_alpha(self.user), expected, places=7)

    def test_idle_lower_than_fresh(self):
        """같은 좋아요 1건이라도 7일 전 활동은 now 활동보다 alpha 가 작다."""
        other = _other_user()
        p_idle = make_post(self.user)
        p_fresh = make_post(other)
        _like(self.user, p_idle, days_ago=7)
        _like(other, p_fresh)
        self.assertGreater(personalization_alpha(other), personalization_alpha(self.user))

    def test_alpha_capped_at_one(self):
        """strength 가 ALPHA_FULL 를 넘으면 1.0 으로 캡(북마크 1.2 × 85 = 102 > 100)."""
        for _ in range(85):
            _bookmark(self.user, make_post(self.user))
        self.assertAlmostEqual(personalization_alpha(self.user), 1.0, places=6)


# ── 코드워드 카운트 누적 ───────────────────────────────────────────────────
class TestBuildCodewordCounts(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = make_shared_user()

    def test_no_interactions_returns_none(self):
        """상호작용 자체가 없으면 None(콜드 스타터)."""
        self.assertIsNone(build_codeword_counts(self.user))

    def test_interactions_without_rec_returns_none(self):
        """상호작용은 있으나 PostRec 가 없으면 누적이 비어 None."""
        post = make_post(self.user)
        _like(self.user, post)  # rec 없음
        self.assertIsNone(build_codeword_counts(self.user))

    def test_empty_codewords_returns_none(self):
        """codewords 가 빈 리스트인 글은 스킵 → 누적 비면 None."""
        post = make_post(self.user)
        make_rec(post, [])
        _like(self.user, post)
        self.assertIsNone(build_codeword_counts(self.user))

    def test_version_mismatch_returns_none(self):
        """글 codebook_version 과 요청 version 이 다르면 코드워드 로드가 안 돼 None."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}], version="v2")
        _like(self.user, post)
        self.assertIsNone(build_codeword_counts(self.user, version="v1"))

    def test_version_carried_in_result(self):
        """결과에 어느 코드북 버전 기준인지 함께 반환."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}], version="v2")
        _like(self.user, post)
        result = build_codeword_counts(self.user, version="v2")
        self.assertIsNotNone(result)
        self.assertEqual(result["version"], "v2")

    def test_single_like_fresh_exact(self):
        """좋아요1(now) × codeword weight → base(0.8) × 감쇠(1.0) × weight."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 7, "weight": 2.0}])
        _like(self.user, post)
        counts = build_codeword_counts(self.user)["counts"]
        self.assertAlmostEqual(counts["7"], 0.8 * 2.0, places=6)
        self.assertEqual(set(counts), {"7"})

    def test_codeword_keys_are_strings(self):
        """codeword 키는 정수여도 문자열로 저장된다."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 10, "weight": 1.0}])
        _like(self.user, post)
        counts = build_codeword_counts(self.user)["counts"]
        self.assertIn("10", counts)
        self.assertTrue(all(isinstance(k, str) for k in counts))

    def test_accumulates_multiple_codewords(self):
        """한 글의 여러 codeword 각각 누적."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}, {"codeword": 2, "weight": 0.5}])
        _like(self.user, post)
        counts = build_codeword_counts(self.user)["counts"]
        self.assertAlmostEqual(counts["1"], 0.8, places=6)
        self.assertAlmostEqual(counts["2"], 0.4, places=6)

    def test_same_codeword_from_multiple_posts_sums(self):
        """서로 다른 글이라도 같은 codeword 면 합산."""
        p1, p2 = make_post(self.user), make_post(self.user)
        make_rec(p1, [{"codeword": 1, "weight": 1.0}])
        make_rec(p2, [{"codeword": 1, "weight": 1.0}])
        _like(self.user, p1)  # 0.8
        _bookmark(self.user, p2)  # 1.2
        counts = build_codeword_counts(self.user)["counts"]
        self.assertAlmostEqual(counts["1"], 0.8 + 1.2, places=6)

    def test_time_decay_applied(self):
        """오래된 상호작용은 시간감쇠(center=60)로 기여가 줄어든다."""
        p_fresh, p_old = make_post(self.user), make_post(self.user)
        make_rec(p_fresh, [{"codeword": 1, "weight": 1.0}])
        make_rec(p_old, [{"codeword": 2, "weight": 1.0}])
        _like(self.user, p_fresh)  # 감쇠 1.0 → 0.8
        _like(self.user, p_old, days_ago=60)  # 감쇠 0.5 → 0.4
        counts = build_codeword_counts(self.user)["counts"]
        self.assertAlmostEqual(counts["1"], 0.8, places=6)
        self.assertAlmostEqual(counts["2"], 0.4, places=6)

    def test_skips_posts_without_rec(self):
        """rec 없는 글의 상호작용은 누적에서 제외."""
        p_rec, p_norec = make_post(self.user), make_post(self.user)
        make_rec(p_rec, [{"codeword": 1, "weight": 1.0}])
        _like(self.user, p_rec)
        _like(self.user, p_norec)  # rec 없음 → 스킵
        counts = build_codeword_counts(self.user)["counts"]
        self.assertEqual(set(counts), {"1"})

    def test_values_rounded_to_six_places(self):
        """누적값은 6자리로 반올림되어 저장된다."""
        post = make_post(self.user)
        make_rec(post, [{"codeword": 5, "weight": 0.1234567}])
        _like(self.user, post)
        v = build_codeword_counts(self.user)["counts"]["5"]
        self.assertEqual(v, round(v, 6))  # 반올림이 실제로 적용됐는지
        self.assertAlmostEqual(v, round(0.8 * 0.1234567, 6), places=9)

    def test_ignores_other_users(self):
        """다른 유저의 상호작용은 섞이지 않는다."""
        other = _other_user()
        post = make_post(self.user)
        make_rec(post, [{"codeword": 1, "weight": 1.0}])
        _like(other, post)  # 다른 유저가 좋아요
        self.assertIsNone(build_codeword_counts(self.user))

    def test_combines_all_interaction_types(self):
        """좋아요/댓글/클릭/북마크가 모두 같은 codeword 에 가중치대로 누적."""
        posts = [make_post(self.user) for _ in range(4)]
        for p in posts:
            make_rec(p, [{"codeword": 1, "weight": 1.0}])
        _like(self.user, posts[0])
        _comment(self.user, posts[1])
        _click(self.user, posts[2])
        _bookmark(self.user, posts[3])
        counts = build_codeword_counts(self.user)["counts"]
        expected = sum(TASTE_WEIGHTS[k] for k in ("like", "comment", "click", "bookmark"))
        self.assertAlmostEqual(counts["1"], expected, places=6)
