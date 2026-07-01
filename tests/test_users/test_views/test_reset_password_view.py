from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from tests.test_core.bases.user_base import UserViewBase


class BaseTest(UserViewBase):

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

    def setUp(self) -> None:
        self.cache_patcher = patch("apps.users.services.reset_password_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)


class ResetPasswordViewTest(BaseTest):

    def test_reset_password_view(self) -> None:
        """정상: 200 + 비밀번호 변경"""
        self.mock_cache.get.return_value = {"email": self.user1.email}

        response = self.client.post(
            reverse("users:reset_password"),
            data={
                "email_token": "valid_token",
                "new_password": "Password@2",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user1.refresh_from_db()
        self.assertTrue(self.user1.check_password("Password@2"))
        self.assertFalse(self.user1.check_password("Password@1"))

    def test_reset_password_missing_email_token(self) -> None:
        """email_token 누락 → serializer 검증 실패 → 400"""
        response = self.client.post(
            reverse("users:reset_password"),
            data={"new_password": "Password@2"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_invalid_password_format(self) -> None:
        """비밀번호 형식 위반(대문자/특수문자 없음) → 400"""
        response = self.client.post(
            reverse("users:reset_password"),
            data={
                "email_token": "valid_token",
                "new_password": "password1",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_invalid_token(self) -> None:
        """토큰 무효/만료(cache.get → None) → 401"""
        self.mock_cache.get.return_value = None

        response = self.client.post(
            reverse("users:reset_password"),
            data={
                "email_token": "expired_token",
                "new_password": "Password@2",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
