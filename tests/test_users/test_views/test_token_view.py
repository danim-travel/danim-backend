from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class TokenViewTest(APITestCase):
    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="testnick",
            name="testname",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

    def setUp(self) -> None:
        self.refresh_token = str(RefreshToken.for_user(self.user))
        # view 레이어는 Redis를 mock (블랙리스트 조회)
        self.cache_patcher = patch("apps.users.services.token_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.mock_cache.get.return_value = None
        self.addCleanup(self.cache_patcher.stop)

    def test_refresh_access_token_success(self) -> None:
        """쿠키의 refresh_token으로 access_token 재발급"""
        self.client.cookies["refresh_token"] = self.refresh_token
        response = self.client.post(reverse("users:token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_refresh_access_token_invalid(self) -> None:
        """유효하지 않은 refresh_token 쿠키 → 403"""
        self.client.cookies["refresh_token"] = "invalid_token"
        response = self.client.post(reverse("users:token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh_missing(self) -> None:
        """refresh_token 쿠키 누락 → 400"""
        response = self.client.post(reverse("users:token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_refresh_blacklisted_token(self) -> None:
        """블랙리스트(로그아웃)된 refresh_token → 403"""
        self.mock_cache.get.return_value = True
        self.client.cookies["refresh_token"] = self.refresh_token
        response = self.client.post(reverse("users:token_refresh"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
