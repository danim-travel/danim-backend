from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import UnauthorizedException, ValidationException
from apps.users.models import User
from apps.users.services.login_logout_service import LoginService


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
        self.service = LoginService()
        self.cache_patcher = patch("apps.users.services.login_logout_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)


class LoginServiceTest(BaseTest):

    def test_login_success(self) -> None:
        """로그인 성공"""
        self.mock_cache.get.return_value = None
        access_token, refresh_token = self.service.login(
            "test@example.com", "Password@1", ""
        )
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)

    def test_login_invalid(self) -> None:
        """잘못된 이메일 또는 비밀번호"""
        with self.assertRaises(UnauthorizedException):
            self.service.login("wrong@example.com", "wrongpassword", "")

    def test_login_blacklist_token(self) -> None:
        """블랙리스트 토큰으로 로그인"""
        old_token = RefreshToken.for_user(self.user)
        self.mock_cache.get.return_value = True
        with self.assertRaises(ValidationException):
            self.service.login("test@example.com", "Password@1", str(old_token))

    def test_login_with_old_refresh_token(self) -> None:
        """기존 refresh_token 있을 때 로그인 성공"""
        old_token = RefreshToken.for_user(self.user)
        self.mock_cache.get.return_value = None
        access_token, refresh_token = self.service.login(
            "test@example.com", "Password@1", str(old_token)
        )
        self.assertIsInstance(access_token, str)
        self.assertIsInstance(refresh_token, str)
        self.mock_cache.set.assert_called_once()
