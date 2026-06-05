from datetime import date
from unittest.mock import patch

from django.test import TestCase
from redis import RedisError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import (
    ForbiddenException,
    InternalServerException,
)
from apps.users.models import User
from apps.users.services.token_service import TokenService


class TokenServiceTest(TestCase):
    """jwt 서비스 레이어 test"""

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
        self.service = TokenService()
        self.cache_patcher = patch("apps.users.services.token_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.mock_cache.get.return_value = None  # 기본: 블랙리스트 아님
        self.addCleanup(self.cache_patcher.stop)

    def test_refresh_access_token_success(self) -> None:
        """refresh_token으로 access_token 발급"""
        refresh = RefreshToken.for_user(self.user)
        access_token = self.service.refresh_access_token(str(refresh))
        self.assertIsInstance(access_token, str)

    def test_refresh_access_token_invalid(self) -> None:
        """유효하지 않은 refresh_token으로 access_token 발급"""
        with self.assertRaises(ForbiddenException):
            self.service.refresh_access_token("invalid_token")

    def test_refresh_blacklisted_token(self) -> None:
        """블랙리스트(로그아웃)된 refresh_token은 재발급 차단(403)"""
        self.mock_cache.get.return_value = True
        refresh = RefreshToken.for_user(self.user)
        with self.assertRaises(ForbiddenException):
            self.service.refresh_access_token(str(refresh))

    def test_refresh_blacklist_redis_error(self) -> None:
        """블랙리스트 조회 중 Redis 장애 → 500"""
        self.mock_cache.get.side_effect = RedisError
        refresh = RefreshToken.for_user(self.user)
        with self.assertRaises(InternalServerException):
            self.service.refresh_access_token(str(refresh))
