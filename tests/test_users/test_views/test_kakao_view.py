from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

FRONT_URI = "http://localhost:3000"


class KakaoLoginViewTest(APITestCase):

    @patch("apps.users.services.kakao_service.KakaoService.build_authorize_url")
    def test_login_redirects_to_kakao(self, mock_build):
        """카카오 로그인 시작 → authorize URL로 302 리다이렉트"""
        mock_build.return_value = "https://kauth.kakao.com/oauth/authorize?fake"

        response = self.client.get(reverse("users:kakao_login"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "https://kauth.kakao.com/oauth/authorize?fake")


@override_settings(FRONT_REDIRECT_URI=FRONT_URI)
class KakaoCallbackViewTest(APITestCase):

    @patch("apps.users.services.kakao_service.KakaoService.kakao_callback")
    def test_callback_redirects_and_sets_cookie(self, mock_callback):
        """콜백 → is_success=true로 리다이렉트 + refresh_token 쿠키 설정"""
        mock_callback.return_value = {
            "access_token": "access",
            "refresh_token": "refresh",
        }

        response = self.client.get(
            reverse("users:kakao_callback"), {"code": "code", "state": "state"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.url,
            f"{FRONT_URI}?provider=kakao&is_success=true",
        )
        self.assertEqual(response.cookies["refresh_token"].value, "refresh")

    @patch("apps.users.services.kakao_service.KakaoService.kakao_callback")
    def test_callback_passes_code_and_state_to_service(self, mock_callback):
        """콜백이 쿼리의 code/state를 service에 그대로 전달"""
        mock_callback.return_value = {
            "access_token": "access",
            "refresh_token": "refresh",
        }

        self.client.get(reverse("users:kakao_callback"), {"code": "abc", "state": "xyz"})

        mock_callback.assert_called_once_with("abc", "xyz")
