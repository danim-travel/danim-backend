from datetime import date
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from apps.core.exceptions.exception import ConflictException
from apps.users.models import User
from apps.users.services.user_update_delete_service import UserUpdateService


class BaseTestCase(TestCase):
    user1: User
    user2: User
    user3: User

    @classmethod
    def setUpTestData(cls):

        # 모든 데이터를 가지고 있는 유저
        cls.user1 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            intro="test_intro",
            birth_day=date(1970, 1, 1),
            profile_img="test_key",
        )

        # 프로필 이미지가 None인 유저
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
        )

    def setUp(self) -> None:
        self.service = UserUpdateService()


class UserUpdateServiceTest(BaseTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.data1 = {
            "nickname": "update_nickname",
            "intro": "update_intro",
            "key": "update_key",
        }

    def test_update_valid(self) -> None:
        """검증된 데이터를 업데이트 할떄"""
        update_user = self.service.user_update(
            user=self.user1,
            data=self.data1,
        )

        self.assertEqual(update_user.nickname, "update_nickname")
        self.assertEqual(update_user.intro, "update_intro")
        self.assertEqual(update_user.profile_img, "update_key")

    def test_update_partial(self) -> None:
        """부분 수정 요청"""
        update_user = self.service.user_update(
            user=self.user1,
            data={
                "nickname": "update_nickname",
            },
        )
        self.assertEqual(update_user.nickname, "update_nickname")
        self.assertEqual(update_user.intro, "test_intro")
        self.assertEqual(update_user.profile_img, "test_key")

    def test_update_nickname_duplicated(self) -> None:
        """중복된 닉네임 요청"""
        with self.assertRaises(ConflictException):
            self.service.user_update(user=self.user1, data={"nickname": "test2"})

    def test_update_integrity_error(self) -> None:
        """save 시 IntegrityError → ConflictException(409)"""
        with patch.object(self.user1, "save", side_effect=IntegrityError):
            with self.assertRaises(ConflictException):
                self.service.user_update(self.user1, {"nickname": "brandnew"})

    def test_update_own_nickname(self) -> None:
        """자기 현재 닉네임 그대로 보내도 중복 아님"""
        update_user = self.service.user_update(
            user=self.user1,
            data={"nickname": "test"},  # user1의 현재 닉네임
        )
        self.assertEqual(update_user.nickname, "test")
