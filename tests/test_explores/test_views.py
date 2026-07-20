from unittest.mock import MagicMock, patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.core.exceptions.exception import ValidationException
from apps.explores import views
from apps.explores.views import ExploresView
from tests.test_explores.utils import make_shared_user

_PATH = "/api/explores/"


def _make_request(user=None):
    request = APIRequestFactory().get(_PATH)
    if user is not None:
        force_authenticate(request, user=user)
    return request


def _query_stub(validated: dict):
    """ExploreQuerySerializer 대역: is_valid 통과 + 통제된 validated_data."""
    serializer = MagicMock()
    instance = serializer.return_value
    instance.is_valid.return_value = True
    instance.validated_data = validated
    return serializer


def _resp_stub(data=None):
    """ExploreResponseSerializer 대역: .data 만 평범한 dict 로 돌려줌."""
    serializer = MagicMock()
    serializer.return_value.data = data if data is not None else {"ok": True}
    return serializer


# ───────────────────────── _page_from_cursor (pure) ─────────────────────────
class PageFromCursorTests(TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(ExploresView._page_from_cursor(None), 0)
        self.assertEqual(ExploresView._page_from_cursor(""), 0)

    def test_valid_int(self):
        self.assertEqual(ExploresView._page_from_cursor("5"), 5)

    def test_negative_raises(self):
        with self.assertRaises(ValidationException):
            ExploresView._page_from_cursor("-1")

    def test_non_int_raises(self):
        with self.assertRaises(ValidationException):
            ExploresView._page_from_cursor("abc")
        with self.assertRaises(ValidationException):
            ExploresView._page_from_cursor("3.5")


# ───────────────────────── 인증 ─────────────────────────
class AuthTests(TestCase):
    def test_anonymous_denied(self):
        response = ExploresView.as_view()(_make_request(user=None))
        self.assertIn(response.status_code, (401, 403))


# ───────────────────────── 피드 분기 ─────────────────────────
class FeedRoutingTests(TestCase):
    def setUp(self):
        self.user = make_shared_user()

    def test_full_page_sets_next_and_threads_service_seed(self):
        results = [object() for _ in range(10)]  # == page_size → has_next
        validated = {
            "search": "",
            "region": None,
            "cursor": "1",
            "page_size": 10,
            "seed": 42,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(
                views, "get_explore_feed", return_value=(results, 999)
            ) as m_feed,
            patch.object(
                views, "build_next", return_value="http://next?cursor=2"
            ) as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            response = ExploresView.as_view()(self._auth())

        self.assertEqual(response.status_code, 200)
        # cursor "1" → page 1, limit=page_size
        self.assertEqual(m_feed.call_args.kwargs["page"], 1)
        self.assertEqual(m_feed.call_args.kwargs["limit"], 10)
        # has_next → 다음 페이지 커서로 build_next, seed 는 서비스가 돌려준 999
        self.assertEqual(m_next.call_args.kwargs["cursor"], "2")
        self.assertEqual(m_next.call_args.kwargs["seed"], 999)
        # 응답 dict: 서비스 seed 가 검증값(42)을 덮어쓰고 실려나감
        payload = m_resp.call_args.args[0]
        self.assertEqual(payload["seed"], 999)
        self.assertEqual(payload["next"], "http://next?cursor=2")
        self.assertEqual(payload["results"], results)

    def test_partial_page_no_next(self):
        results = [object() for _ in range(5)]  # < page_size → has_next False
        validated = {
            "search": "",
            "region": None,
            "cursor": None,
            "page_size": 10,
            "seed": 7,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(views, "get_explore_feed", return_value=(results, 7)) as m_feed,
            patch.object(views, "build_next") as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            ExploresView.as_view()(self._auth())

        self.assertEqual(m_feed.call_args.kwargs["page"], 0)  # cursor None → page 0
        m_next.assert_not_called()
        payload = m_resp.call_args.args[0]
        self.assertIsNone(payload["next"])
        self.assertEqual(payload["results"], results)

    def _auth(self):
        return _make_request(self.user)


# ───────────────────────── 검색 분기 ─────────────────────────
class SearchRoutingTests(TestCase):
    def setUp(self):
        self.user = make_shared_user()

    def test_decodes_cursor_and_sets_next(self):
        feeds = [object(), object()]
        validated = {
            "search": "hello",
            "region": None,
            "cursor": "Cur5",
            "page_size": 10,
            "seed": 0,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(views, "decode_cursor", return_value=321) as m_dec,
            patch.object(
                views, "feeds_for_search", return_value=(feeds, "NEXTCUR", 0)
            ) as m_search,
            patch.object(
                views, "build_next", return_value="http://next?cursor=NEXTCUR"
            ) as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            response = ExploresView.as_view()(_make_request(self.user))

        self.assertEqual(response.status_code, 200)
        m_dec.assert_called_once_with("Cur5")
        # 디코드된 커서가 그대로 서비스에 (positional)
        self.assertEqual(m_search.call_args.args, ("hello", 321))
        # new_cursor 가 truthy → search+new_cursor 로 next 생성
        self.assertEqual(m_next.call_args.kwargs["search"], "hello")
        self.assertEqual(m_next.call_args.kwargs["cursor"], "NEXTCUR")
        payload = m_resp.call_args.args[0]
        self.assertEqual(payload["results"], feeds)
        self.assertEqual(payload["next"], "http://next?cursor=NEXTCUR")

    def test_without_cursor_skips_decode_and_no_next(self):
        validated = {
            "search": "hi",
            "region": None,
            "cursor": None,
            "page_size": 10,
            "seed": 0,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(views, "decode_cursor") as m_dec,
            patch.object(
                views, "feeds_for_search", return_value=([], None, 0)
            ) as m_search,
            patch.object(views, "build_next") as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            ExploresView.as_view()(_make_request(self.user))

        m_dec.assert_not_called()
        self.assertEqual(m_search.call_args.args, ("hi", None))
        m_next.assert_not_called()  # new_cursor None
        self.assertIsNone(m_resp.call_args.args[0]["next"])


# ───────────────────────── 지역 분기 ─────────────────────────
class RegionRoutingTests(TestCase):
    def setUp(self):
        self.user = make_shared_user()

    def test_search_takes_priority_over_region(self):
        """search 와 region 이 둘 다 오면 search 가 우선."""
        validated = {
            "search": "hello",
            "region": "강원",
            "cursor": None,
            "page_size": 10,
            "seed": 0,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(
                views, "feeds_for_search", return_value=([], None, 0)
            ) as m_search,
            patch.object(views, "feeds_for_region") as m_region,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            ExploresView.as_view()(_make_request(self.user))

        m_search.assert_called_once()
        m_region.assert_not_called()

    def test_decodes_cursor_and_sets_next(self):
        feeds = [object(), object()]
        validated = {
            "search": "",
            "region": "강원",
            "cursor": "Cur5",
            "page_size": 10,
            "seed": 0,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(views, "decode_cursor", return_value=321) as m_dec,
            patch.object(
                views, "feeds_for_region", return_value=(feeds, "NEXTCUR", 0)
            ) as m_region,
            patch.object(
                views, "build_next", return_value="http://next?cursor=NEXTCUR"
            ) as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            response = ExploresView.as_view()(_make_request(self.user))

        self.assertEqual(response.status_code, 200)
        m_dec.assert_called_once_with("Cur5")
        self.assertEqual(m_region.call_args.args, ("강원", 321))
        self.assertEqual(m_next.call_args.kwargs["region"], "강원")
        self.assertEqual(m_next.call_args.kwargs["cursor"], "NEXTCUR")
        payload = m_resp.call_args.args[0]
        self.assertEqual(payload["results"], feeds)
        self.assertEqual(payload["next"], "http://next?cursor=NEXTCUR")

    def test_without_cursor_skips_decode_and_no_next(self):
        validated = {
            "search": "",
            "region": "강원",
            "cursor": None,
            "page_size": 10,
            "seed": 0,
        }

        with (
            patch.object(views, "ExploreQuerySerializer", _query_stub(validated)),
            patch.object(views, "decode_cursor") as m_dec,
            patch.object(
                views, "feeds_for_region", return_value=([], None, 0)
            ) as m_region,
            patch.object(views, "build_next") as m_next,
            patch.object(views, "ExploreResponseSerializer", _resp_stub()) as m_resp,
        ):
            ExploresView.as_view()(_make_request(self.user))

        m_dec.assert_not_called()
        self.assertEqual(m_region.call_args.args, ("강원", None))
        m_next.assert_not_called()
        self.assertIsNone(m_resp.call_args.args[0]["next"])
