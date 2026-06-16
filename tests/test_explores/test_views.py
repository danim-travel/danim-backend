from unittest.mock import ANY, patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from tests.test_explores.utils import user_and_post

User = get_user_model()


class ExploresViewTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user, _ = user_and_post()

    def setUp(self):
        self.url = reverse(
            "explores:explore"
        )  # urls.py의 name으로. 없으면 "/api/explores/"
        self.client.force_authenticate(user=self.user)

    # 인증 안 된 요청 → 401
    def test_requires_auth(self):
        self.client.force_authenticate(user=None)  # 인증 해제
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 401)

    # search 없음 → call_posts 호출, feeds_for_search 안 탐
    @patch("apps.explores.views.feeds_for_search")
    @patch("apps.explores.views.call_posts")
    def test_no_search_calls_call_posts(self, mock_call_posts, mock_search):
        mock_call_posts.return_value = ([], None, 0)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 200)
        mock_call_posts.assert_called_once_with(None)  # cursor 없음 → None
        mock_search.assert_not_called()

    # search 있음 → feeds_for_search 호출, call_posts 안 탐
    @patch("apps.explores.views.call_posts")
    @patch("apps.explores.views.feeds_for_search")
    def test_search_calls_feeds_for_search(self, mock_search, mock_call_posts):
        mock_search.return_value = ([], None, 0)

        res = self.client.get(self.url, {"search": "cat"})

        self.assertEqual(res.status_code, 200)
        mock_search.assert_called_once_with("cat", None)
        mock_call_posts.assert_not_called()

    # raw_cursor 있음 → decode되고 그 결과가 서비스로 전달
    @patch("apps.explores.views.call_posts")
    @patch("apps.explores.views.decode_cursor")
    def test_cursor_is_decoded_and_passed(self, mock_decode, mock_call_posts):
        mock_decode.return_value = "DECODED"
        mock_call_posts.return_value = ([], None, 0)

        res = self.client.get(self.url, {"cursor": "rawcur"})

        self.assertEqual(res.status_code, 200)
        mock_decode.assert_called_once_with("rawcur")
        mock_call_posts.assert_called_once_with("DECODED")

    # raw_cursor 없음 → decode 호출 안 됨
    @patch("apps.explores.views.call_posts")
    @patch("apps.explores.views.decode_cursor")
    def test_no_cursor_skips_decode(self, mock_decode, mock_call_posts):
        mock_call_posts.return_value = ([], None, 0)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 200)
        mock_decode.assert_not_called()

    # new_cursor 있음 → build_next 호출되고 next에 반영
    @patch("apps.explores.views.build_next")
    @patch("apps.explores.views.call_posts")
    def test_next_url_built_when_new_cursor(self, mock_call_posts, mock_build_next):
        mock_call_posts.return_value = ([], "NEWCUR", 0)
        mock_build_next.return_value = "http://x/next"

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 200)
        mock_build_next.assert_called_once_with(None, "NEWCUR", ANY)
        self.assertEqual(res.data["next"], "http://x/next")

    # new_cursor 없음 → next는 None
    @patch("apps.explores.views.build_next")
    @patch("apps.explores.views.call_posts")
    def test_next_is_none_without_new_cursor(self, mock_call_posts, mock_build_next):
        mock_call_posts.return_value = ([], None, 0)

        res = self.client.get(self.url)

        self.assertEqual(res.status_code, 200)
        mock_build_next.assert_not_called()
        self.assertIsNone(res.data["next"])
