from django.test import TestCase

from apps.users.serializers.login_logout_serializer import LoginSerializer


class LoginSerializerTest(TestCase):

    def test_login_serializer(self) -> None:
        """이메일 비밀번호 검증 serializer"""
        serializer = LoginSerializer(
            data={
                "email": "test@example.com",
                "password": "Password@1",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_login_without_email(self) -> None:
        """이메일 없는 로그인 시도"""
        serializer = LoginSerializer(
            data={
                "password": "Password@1",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_login_without_password(self) -> None:
        """비밀번호 없는 로그인 시도"""
        serializer = LoginSerializer(
            data={
                "email": "test@example.com",
            }
        )
        self.assertFalse(serializer.is_valid())
