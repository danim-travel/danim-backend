from datetime import date

from django.test import TestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import ForbiddenException
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

    def test_refresh_access_token_success(self) -> None:
        """refresh_token으로 access_token 발급"""
        refresh = RefreshToken.for_user(self.user)
        access_token = self.service.refresh_access_token(str(refresh))
        self.assertIsInstance(access_token, str)

    def test_refresh_access_token_invalid(self) -> None:
        """유효하지 않은 refresh_token으로 access_token 발급"""
        with self.assertRaises(ForbiddenException):
            self.service.refresh_access_token("invalid_token")
