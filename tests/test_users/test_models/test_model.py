from django.test import TestCase

from apps.users.models import User


class UserTest(TestCase):

    def test_create_user(self) -> None:
        """일반 유저 생성을 위한 test 함수"""
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day="1970-01-01",
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.nickname, "testnickname")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.name, "test")
        self.assertTrue(self.user.check_password("Password@123"))
        self.assertEqual(self.user.phone_number, "01012345678")
        self.assertEqual(self.user.birth_day, "1970-01-01")
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_active)

    def test_create_superuser(self) -> None:
        """superuser을 생성하기 위한 test 함수"""
        self.superuser = User.objects.create_superuser(
            email="super@example.com",
            name="supername",
            nickname="supernickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day="1970-01-01",
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            is_superuser=True,
        )
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.check_password("Password@123"))
