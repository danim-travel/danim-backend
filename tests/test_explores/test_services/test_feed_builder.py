from unittest.mock import patch

from django.test import SimpleTestCase, TestCase

from apps.core.storage.s3 import s3_svc
from apps.core.utils.base62 import encode_cursor
from apps.explores.services.feed_builder import build_feed, page_from_ids
from apps.posts.models import Post
from tests.test_explores.utils import user_and_post


class PageFromIdsTest(SimpleTestCase):
    def test_first_page_no_cursor(self) -> None:
        page_ids, new_cursor = page_from_ids(["a", "b", "c", "d", "e"], None, 2)
        self.assertEqual(page_ids, ["a", "b"])
        self.assertEqual(new_cursor, encode_cursor("b"))

    def test_middle_page_with_valid_cursor(self) -> None:
        page_ids, new_cursor = page_from_ids(["a", "b", "c", "d", "e"], "b", 2)
        self.assertEqual(page_ids, ["c", "d"])
        self.assertEqual(new_cursor, encode_cursor("d"))

    def test_last_page_is_partial_but_still_returns_a_cursor(self) -> None:
        """진짜 끝인지는 이 반환값만으로 알 수 없다 -> 다음 호출이 빈 결과인지로 판단하는 구조."""
        page_ids, new_cursor = page_from_ids(["a", "b", "c"], "b", 2)
        self.assertEqual(page_ids, ["c"])
        self.assertEqual(new_cursor, encode_cursor("c"))

    def test_cursor_at_last_id_returns_empty(self) -> None:
        page_ids, new_cursor = page_from_ids(["a", "b", "c"], "c", 2)
        self.assertEqual(page_ids, [])
        self.assertIsNone(new_cursor)

    def test_cursor_not_in_ids_falls_back_to_first_page(self) -> None:
        """캐시 재빌드로 커서가 목록에서 사라진 경우 -> 400 대신 첫 페이지로 폴백."""
        page_ids, new_cursor = page_from_ids(["a", "b", "c", "d", "e"], "NOT-IN-LIST", 2)
        self.assertEqual(page_ids, ["a", "b"])
        self.assertEqual(new_cursor, encode_cursor("b"))

    def test_empty_ids_returns_empty_page(self) -> None:
        page_ids, new_cursor = page_from_ids([], None, 10)
        self.assertEqual(page_ids, [])
        self.assertIsNone(new_cursor)


class BuildFeedTest(TestCase):
    def setUp(self) -> None:
        patcher = patch.object(
            s3_svc,
            "create_download_presigned_url",
            side_effect=lambda key: f"https://signed/{key}",
        )
        self.mock_s3 = patcher.start()
        self.addCleanup(patcher.stop)

    def test_preserves_page_ids_order(self) -> None:
        """정렬은 page_ids 순서를 따르며, DB 조회 순서(기본 오름차순)와 무관하다."""
        user, post_a = user_and_post()
        post_b = Post.objects.create(user=user, title="t2", thumbnail="t2.jpg")

        feed = build_feed([post_b.id, post_a.id])

        self.assertEqual([f.id for f in feed], [post_b.id, post_a.id])

    def test_maps_fields_and_presigns_thumbnail(self) -> None:
        user, post = user_and_post()
        post.like_count = 3
        post.comment_count = 2
        post.thumbnail_width = 100
        post.thumbnail_height = 200
        post.save(
            update_fields=[
                "like_count",
                "comment_count",
                "thumbnail_width",
                "thumbnail_height",
            ]
        )

        feed = build_feed([post.id])

        self.assertEqual(len(feed), 1)
        result = feed[0]
        self.assertEqual(result.id, post.id)
        self.assertEqual(result.like_count, 3)
        self.assertEqual(result.comment_count, 2)
        self.assertEqual(result.thumbnail_width, 100)
        self.assertEqual(result.thumbnail_height, 200)
        self.assertEqual(result.thumbnail, f"https://signed/{post.thumbnail}")

    def test_empty_page_ids_returns_empty_list(self) -> None:
        self.assertEqual(build_feed([]), [])
