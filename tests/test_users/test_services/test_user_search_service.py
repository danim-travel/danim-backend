from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User
from apps.users.services.user_search_service import UserSearchService


class UserSearchServiceTestCase(TestCase):
    user1: User
    user2: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user1 = User.objects.create_user(
            email="test1@example.com",
            password="Password@1",
            nickname="test_nick1",
            name="tim",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

        cls.user2 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test_nick2",
            name="sam",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

    def setUp(self) -> None:
        self.service = UserSearchService()

    def test_user_search(self) -> None:
        """유저 검색 서비스 test"""
        result = self.service.search_users(self.user1.name)

        self.assertEqual(result.count(), 1)
        self.assertIn(self.user1, result)
        self.assertNotIn(self.user2, result)

    def test_user_search_None(self) -> None:
        """유저 검색시 빈값 입력"""
        with self.assertRaises(ValidationException):
            self.service.search_users("")
