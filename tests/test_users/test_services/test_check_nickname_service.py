from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ConflictException
from apps.users.models import User
from apps.users.services.check_nickname_service import CheckNicknameService


class CheckNicknameServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = CheckNicknameService()

    def test_check_nickname_success(self) -> None:
        """중복 인증 통과"""
        new_nickname = self.service.check_duplicate_nickname("new_nickname")
        self.assertEqual(new_nickname, "new_nickname")

    def test_check_nickname_fail(self) -> None:
        """중복 인증 실패"""
        User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="nickname",
            name="testname",
            birth_day=date(1999, 1, 1),
        )
        with self.assertRaises(ConflictException):
            self.service.check_duplicate_nickname("nickname")
