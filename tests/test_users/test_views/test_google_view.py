from unittest.mock import patch

from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase


class GoogleLoginViewTest(APITestCase):

    @patch("apps.users.services.google_service.GoogleService.build_authorize_url")
    def test_login_redirects_to_google(self, mock_build):
        """구글 로그인 시작 → authorize URL로 302 리다이렉트"""
        mock_build.return_value = "https://accounts.google.com/o/oauth2/v2/auth?fake"

        response = self.client.get(reverse("users:google_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url, "https://accounts.google.com/o/oauth2/v2/auth?fake"
        )


class GoogleCallbackViewTest(APITestCase):

    @patch("apps.users.services.google_service.GoogleService.google_callback")
    def test_callback_redirects_and_sets_cookie(self, mock_callback):
        """콜백 → login/success로 리다이렉트 + refresh_token 쿠키 설정"""
        mock_callback.return_value = {
            "access_token": "access",
            "refresh_token": "refresh",
        }

        response = self.client.get(
            reverse("users:google_callback"), {"code": "code", "state": "state"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{settings.FRONT_REDIRECT_URI}/login/success")
        self.assertEqual(response.cookies["refresh_token"].value, "refresh")

    @patch("apps.users.services.google_service.GoogleService.google_callback")
    def test_callback_passes_code_and_state_to_service(self, mock_callback):
        """콜백이 쿼리의 code/state를 service에 그대로 전달"""
        mock_callback.return_value = {
            "access_token": "access",
            "refresh_token": "refresh",
        }

        self.client.get(reverse("users:google_callback"), {"code": "abc", "state": "xyz"})

        mock_callback.assert_called_once_with("abc", "xyz")
