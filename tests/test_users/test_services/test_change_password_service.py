from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ForbiddenException, ValidationException
from apps.users.models import User
from apps.users.services.change_password_service import ChangePasswordService


class ChangePasswordServiceTest(TestCase):
    user: User
    user2: User
    service = ChangePasswordService()

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
            login_type="email",
        )
        cls.user2 = User.objects.create_user(
            email="owner2@example.com",
            password="Password@1",
            nickname="owner",
            name="owner2",
            birth_day=date(1990, 1, 1),
            login_type="kakao",
        )

    def test_change_password(self) -> None:
        self.service.change_password(
            user=self.user,
            password="Password@1",
            new_password="Password@2",
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
            )

    def test_change_password_login_type_invalid(self) -> None:
        """소셜 유저 → ForbiddenException"""
        with self.assertRaises(ForbiddenException):
            self.service.change_password(
                user=self.user2,
                password="Password@1",
                new_password="Password@2",
            )
