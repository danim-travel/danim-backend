from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class BaseViewTest(APITestCase):
    user: User

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="testnick",
            name="testname",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

    def setUp(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        self.refresh_token = str(refresh)


class TokenViewTest(BaseViewTest):
    def test_refresh_access_token_success(self) -> None:
        """유효한 refresh_token으로 access_token 재발급"""
        response = self.client.post(
            reverse("users:token_refresh"), {"refresh_token": self.refresh_token}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_refresh_access_token_invalid(self) -> None:
        """유효하지 않은 refresh_token"""
        response = self.client.post(
            reverse("users:token_refresh"), {"refresh_token": "invalid_token"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_token_refresh_missing(self) -> None:
        """refresh_token 누락"""
        response = self.client.post(
            reverse("users:token_refresh"),
            {},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
