from datetime import date
from unittest.mock import patch

from redis import RedisError

from apps.core.exceptions.exception import (
    InternalServerException,
    UnauthorizedException,
)
from apps.users.models import LoginType, User
from apps.users.services.reset_password_service import ResetPasswordService
from tests.test_core.bases.user_base import UserBase


class BaseTest(UserBase):
    service = ResetPasswordService()

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()

    def setUp(self) -> None:
        self.cache_patcher = patch("apps.users.services.reset_password_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)


class ResetPasswordServiceTest(BaseTest):

    def test_reset_password_valid(self) -> None:
        """정상: 토큰이 유효하고 유저가 존재하면 비밀번호가 실제로 바뀐다."""
        # Arrange: 비밀번호 변경 전용 유저 + cache.get이 토큰에 매핑된 이메일을 돌려준다
        reset_user = User.objects.create_user(
            email="reset_target@example.com",
            password="Password@1",
            nickname="reset_target",
            name="reset_target",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.EMAIL,
        )
        self.mock_cache.get.return_value = {"email": reset_user.email}

        # Act
        self.service.reset_password("valid_token", "NewPassword@1")

        # Assert: DB에서 다시 읽어 비번 변경 확인 + 토큰 삭제 확인
        reset_user.refresh_from_db()
        self.assertTrue(reset_user.check_password("NewPassword@1"))
        self.assertFalse(reset_user.check_password("Password@1"))
        self.mock_cache.delete.assert_called_once()

    def test_reset_password_redis_error(self) -> None:
        """Redis 장애: cache.get이 실패하면 InternalServerException."""
        self.mock_cache.get.side_effect = RedisError

        with self.assertRaises(InternalServerException):
            self.service.reset_password("any_token", "NewPassword@1")

    def test_reset_password_invalid_token(self) -> None:
        """토큰 무효/만료: cache.get이 None이면 UnauthorizedException."""
        self.mock_cache.get.return_value = None

        with self.assertRaises(UnauthorizedException):
            self.service.reset_password("expired_token", "NewPassword@1")

    def test_reset_password_user_not_found(self) -> None:
        """토큰은 유효하나 해당 이메일 유저가 없으면 UnauthorizedException."""
        self.mock_cache.get.return_value = {"email": "nobody@example.com"}

        with self.assertRaises(UnauthorizedException):
            self.service.reset_password("valid_token", "NewPassword@1")

    def test_reset_password_social_user_blocked(self) -> None:
        """소셜 유저(login_type != EMAIL)는 조회에서 걸러져 UnauthorizedException."""
        self.mock_cache.get.return_value = {"email": self.social_user.email}

        with self.assertRaises(UnauthorizedException):
            self.service.reset_password("valid_token", "NewPassword@1")
