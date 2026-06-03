from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import UnauthorizedException, ValidationException
from apps.users.models import User
from apps.users.services.login_logout_service import LoginService, LogoutService


class BaseTest(TestCase):
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
        self.login_service = LoginService()
        self.logout_service = LogoutService()
        self.cache_patcher = patch("apps.users.services.login_logout_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)


class LoginServiceTest(BaseTest):

    def test_login_success(self) -> None:
        """로그인 성공"""
        self.mock_cache.get.return_value = None
        access_token, refresh_token = self.login_service.login(
            "test@example.com", "Password@1", ""
        )
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)

    def test_login_invalid(self) -> None:
        """잘못된 이메일 또는 비밀번호"""
        with self.assertRaises(UnauthorizedException):
            self.login_service.login("wrong@example.com", "wrongpassword", "")

    def test_login_with_invalid_old_token(self) -> None:
        """손상된 기존 refresh_token이 있어도 로그인은 성공"""
        access_token, refresh_token = self.login_service.login(
            "test@example.com", "Password@1", "invalid_token"
        )
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)

    def test_login_with_old_refresh_token(self) -> None:
        """기존 refresh_token 있을 때 로그인 성공"""
        old_token = RefreshToken.for_user(self.user)
        self.mock_cache.get.return_value = None
        access_token, refresh_token = self.login_service.login(
            "test@example.com", "Password@1", str(old_token)
        )
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)
        self.mock_cache.set.assert_called_once()


class LogoutServiceTest(BaseTest):

    def test_logout_success(self) -> None:
        """로그아웃 성공"""
        token = RefreshToken.for_user(self.user)
        self.mock_cache.get.return_value = None
        self.logout_service.logout(str(token))
        self.mock_cache.set.assert_called_once()

    def test_logout_without_refresh_token(self) -> None:
        """refresh_token 없음"""
        with self.assertRaises(ValidationException):
            self.logout_service.logout("")

    def test_logout_with_invalid_token(self) -> None:
        """손상된 refresh_token으로 로그아웃해도 예외 없이 처리"""
        self.logout_service.logout("invalid_token")
        self.mock_cache.set.assert_not_called()
