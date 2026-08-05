from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import decode_cursor
from apps.explores.services.region import REGION_PREFIXES, feeds_for_region
from apps.posts.models import Location, Post, PostSpot
from tests.test_explores.utils import user_and_post

LOCMEM = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@override_settings(CACHES=LOCMEM)
class RegionFeedTest(TestCase):
    # REGION_PREFIXES 를 그대로 참조하지 않고 하드코딩한 스냅샷.
    # 실제 REGION_PREFIXES 에서 항목이 지워지면 아래 두 테스트가 이 스냅샷과의
    # 불일치/실매칭 실패로 잡아낸다 (REGION_PREFIXES 를 직접 순회하면 지워진 항목은
    # 순회 대상에서도 같이 사라져서 회귀를 못 잡는다).
    _EXPECTED_PREFIXES = {
        "서울": ["서울"],
        "경기": ["경기"],
        "인천": ["인천"],
        "강원": ["강원"],
        "충청": ["대전", "세종", "충청남도", "충남", "충청북도", "충북"],
        "전라": ["광주", "전라남도", "전남", "전라북도", "전북"],
        "경상": ["대구", "부산", "울산", "경상북도", "경북", "경상남도", "경남"],
        "제주": ["제주"],
    }

    def setUp(self) -> None:
        cache.clear()

    def tearDown(self) -> None:
        cache.clear()

    def _add_spot(self, post, *, road="", address="", order=0):
        location = Location.objects.create(
            address_name=address,
            road_address_name=road,
            place_name="",
            x=127.0,
            y=37.5,
        )
        return PostSpot.objects.create(post=post, location=location, order=order)

    def test_unknown_region_raises(self):
        with self.assertRaises(ValidationException):
            feeds_for_region("도쿄", None)

    def test_matches_old_administrative_name(self):
        """행정구역 개편 전 명칭(강원도)도 매칭돼야 한다."""
        _, post = user_and_post()
        self._add_spot(post, road="강원도 춘천시 어딘가 1")

        feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual([f.id for f in feed], [post.id])

    def test_matches_new_administrative_name(self):
        """행정구역 개편 후 명칭(강원특별자치도)도 매칭돼야 한다."""
        _, post = user_and_post()
        self._add_spot(post, road="강원특별자치도 춘천시 어딘가 1")

        feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual([f.id for f in feed], [post.id])

    def test_matches_grouped_metro_city(self):
        """충청 그룹에는 대전광역시 같은 광역시도 포함된다."""
        _, post = user_and_post()
        self._add_spot(post, road="대전광역시 유성구 어딘가 1")

        feed, _, _ = feeds_for_region("충청", None)

        self.assertEqual([f.id for f in feed], [post.id])

    def test_no_match_returns_empty(self):
        _, post = user_and_post()
        self._add_spot(post, road="서울특별시 강남구 어딘가 1")

        feed, next_cursor, _ = feeds_for_region("제주", None)

        self.assertEqual(feed, [])
        self.assertIsNone(next_cursor)

    def test_ignores_other_regions(self):
        """다른 지역 주소를 가진 게시글은 안 걸려야 한다."""
        _, seoul_post = user_and_post()
        self._add_spot(seoul_post, road="서울특별시 강남구 어딘가 1")

        feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual(feed, [])

    def test_sorted_by_like_count_desc(self):
        """인기순(좋아요 많은 순)으로 정렬돼야 한다."""
        user, low = user_and_post()
        low.like_count = 1
        low.save(update_fields=["like_count"])
        self._add_spot(low, road="강원도 춘천시 1")

        high = Post.objects.create(
            user=user, title="t2", thumbnail="t2.jpg", like_count=10
        )
        self._add_spot(high, road="강원도 원주시 2")

        feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual([f.id for f in feed], [high.id, low.id])

    def test_multiple_spots_do_not_duplicate_post(self):
        """한 게시글이 매칭되는 스팟을 여러 개 가져도 결과에 1번만 나온다."""
        _, post = user_and_post()
        self._add_spot(post, road="강원도 춘천시 1", order=0)
        self._add_spot(post, road="강원특별자치도 원주시 2", order=1)

        feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual(len(feed), 1)
        self.assertEqual(feed[0].id, post.id)

    def test_cache_hit_skips_query(self):
        _, post = user_and_post()
        self._add_spot(post, road="강원도 춘천시 1")
        feeds_for_region("강원", None)  # 캐시 채움

        with self.assertNumQueries(1):  # Post.objects.filter(id__in=page_ids) 1번만
            feed, _, _ = feeds_for_region("강원", None)

        self.assertEqual([f.id for f in feed], [post.id])

    def test_cursor_pagination(self):
        """feeds_for_region 은 이미 디코드된 post_id 를 커서로 받는다(뷰가 decode_cursor 를 먼저 호출)."""
        user, _ = user_and_post()
        for i in range(15):
            p = Post.objects.create(
                user=user, title=f"t{i}", thumbnail="t.jpg", like_count=15 - i
            )
            self._add_spot(p, road="강원도 춘천시", order=i)

        first_page, encoded_cursor, _ = feeds_for_region("강원", None)
        self.assertEqual(len(first_page), 10)

        decoded_cursor = decode_cursor(encoded_cursor)
        second_page, next_cursor, _ = feeds_for_region("강원", decoded_cursor)
        self.assertEqual(len(second_page), 5)
        # 15개 중 마지막 5개라 이 페이지도 비어있진 않으므로 next_cursor 는 여전히 옴
        # (search.py 와 동일하게, 진짜 끝은 "다음 호출이 빈 결과"로 판단하는 구조).
        self.assertIsNotNone(next_cursor)

        third_page, third_cursor, _ = feeds_for_region("강원", decode_cursor(next_cursor))
        self.assertEqual(third_page, [])
        self.assertIsNone(third_cursor)

    def test_all_region_groups_defined(self):
        expected = {"서울", "경기", "인천", "강원", "충청", "전라", "경상", "제주"}
        self.assertEqual(set(REGION_PREFIXES.keys()), expected)

    def test_registered_prefixes_match_expected_snapshot(self):
        """REGION_PREFIXES 내용이 스냅샷과 정확히 같아야 한다.
        아래 test_expected_prefixes_actually_match 와 함께가 아니면 무의미하다:
        여기서 항목이 지워지면 이 테스트가 즉시 실패해서 잡아낸다
        (REGION_PREFIXES.items() 를 그대로 순회하는 테스트는 반대로,
        항목이 지워지는 순간 순회 대상 자체가 사라져서 회귀를 못 잡는다)."""
        self.assertEqual(REGION_PREFIXES, self._EXPECTED_PREFIXES)

    def test_expected_prefixes_actually_match(self):
        """스냅샷에 있는 정식명/축약형 문자열 각각이 실제로 DB 매칭까지 이어지는지 검증.
        address_name 필드로만 매칭시켜 road_address_name 편중도 없앤다."""
        user, _ = user_and_post()
        for group, prefixes in self._EXPECTED_PREFIXES.items():
            for prefix in prefixes:
                with self.subTest(group=group, prefix=prefix):
                    cache.clear()
                    post = Post.objects.create(user=user, title="t", thumbnail="t.jpg")
                    self._add_spot(post, address=f"{prefix} 어딘가 1")

                    feed, _, _ = feeds_for_region(group, None)

                    self.assertIn(
                        post.id,
                        [f.id for f in feed],
                        f"{group!r} 그룹이 address_name 접두어 {prefix!r} 를 매칭하지 못함",
                    )

    def test_matches_abbreviated_directional_province(self):
        """전라남도/전라북도처럼 남/북이 붙는 도(道)는 축약형이 정식명의 문자열 접두어가
        아니다(전남 != 전라남도 앞 2글자). Kakao가 축약형만 줄 때를 대비한 매칭 확인."""
        _, post = user_and_post()
        self._add_spot(post, road="전남 완주군 어딘가 1")

        feed, _, _ = feeds_for_region("전라", None)

        self.assertEqual([f.id for f in feed], [post.id])

    def test_cursor_miss_falls_back_to_first_page(self) -> None:
        """캐시 재빌드 등으로 커서가 목록에서 사라지면 400 대신 첫 페이지로 폴백한다."""
        _, post = user_and_post()
        self._add_spot(post, road="강원도 춘천시 1")

        feed, new_cursor, seed = feeds_for_region("강원", "NOT-A-REAL-POST-ID")
        expected_feed, expected_cursor, expected_seed = feeds_for_region("강원", None)

        self.assertEqual([f.id for f in feed], [f.id for f in expected_feed])
        self.assertEqual(new_cursor, expected_cursor)
        self.assertEqual(seed, expected_seed)
