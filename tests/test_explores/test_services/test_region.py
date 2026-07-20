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
