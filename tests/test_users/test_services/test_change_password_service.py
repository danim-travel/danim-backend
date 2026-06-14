from datetime import date
from unittest.mock import patch

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import ForbiddenException, ValidationException
from apps.users.models import LoginType, User
from apps.users.redis_keys import LoginRedisKey
from apps.users.services.change_password_service import ChangePasswordService


class ChangePasswordServiceTest(TestCase):
    user: User
    user2: User
    service = ChangePasswordService()

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.EMAIL,
        )
        cls.user2 = User.objects.create_user(
            email="owner2@example.com",
            password="Password@1",
            nickname="owner2_nick",
            name="owner2",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.KAKAO,
        )

    def test_change_password(self) -> None:
        """정상: 비밀번호가 실제로 바뀐다"""
        self.service.change_password(
            user=self.user,
            password="Password@1",
            new_password="Password@2",
            refresh_token="",
        )
        self.assertTrue(self.user.check_password("Password@2"))
        self.assertFalse(self.user.check_password("Password@1"))

    def test_change_password_invalid(self) -> None:
        """현재 비밀번호 틀림 → ValidationException"""
        with self.assertRaises(ValidationException):
            self.service.change_password(
                user=self.user,
                password="WrongPassword@1",
                new_password="Password@2",
                refresh_token="",
            )

    def test_change_password_login_type_invalid(self) -> None:
        """소셜 유저 → ForbiddenException"""
        with self.assertRaises(ForbiddenException):
            self.service.change_password(
                user=self.user2,
                password="Password@1",
                new_password="Password@2",
                refresh_token="",
            )

    @patch("apps.users.services.login_logout_service.cache")
    def test_change_password_blacklists_refresh_token(self, mock_cache) -> None:
        """변경 성공 시 전달된 refresh_token이 블랙리스트에 등록된다"""
        token = RefreshToken.for_user(self.user)

        self.service.change_password(
            user=self.user,
            password="Password@1",
            new_password="Password@2",
            refresh_token=str(token),
        )

        mock_cache.set.assert_called_once()
        called_key = mock_cache.set.call_args.args[0]
        self.assertEqual(called_key, LoginRedisKey.blacklist(token["jti"]))
