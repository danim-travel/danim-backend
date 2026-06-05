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
            nickname="test",
            name="test",
            birth_day=date(1970, 1, 1),
            is_active=True,
        )


class LoginViewTest(BaseViewTest):

    def test_login_success(self) -> None:
        """로그인 성공"""
        response = self.client.post(
            reverse("users:login"),
            {"email": "test@example.com", "password": "Password@1"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_invalid(self) -> None:
        """잘못된 이메일 비밀번호"""
        response = self.client.post(
            reverse("users:login"),
            {"email": "wrong@example.com", "password": "wrongpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_without_email(self) -> None:
        """이메일 누락"""
        response = self.client.post(reverse("users:login"), {"password": "Password@1"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_without_password(self) -> None:
        """비밀번호 누락"""
        response = self.client.post(reverse("users:login"), {"email": "test@example.com"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LogoutViewTest(BaseViewTest):

    def test_logout_success(self) -> None:
        """로그아웃 성공"""
        refresh_token = str(RefreshToken.for_user(self.user))
        access_token = str(RefreshToken.for_user(self.user).access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.client.cookies["refresh_token"] = str(refresh_token)

        response = self.client.post(
            reverse("users:logout"),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_without_refresh_token(self) -> None:
        """refresh_token 없이 로그아웃"""
        access_token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthorized(self) -> None:
        """인증 없이 로그아웃"""
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
