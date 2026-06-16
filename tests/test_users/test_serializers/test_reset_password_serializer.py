from django.test import TestCase

from apps.users.serializers.reset_password_serializer import (
    ResetPasswordRequestSerializer,
)


class ResetPasswordSerializerTest(TestCase):

    def test_reset_password(self) -> None:
        """성공 serializer"""
        serializer = ResetPasswordRequestSerializer(
            data={
                "email_token": "fnsljfdlksmkl",
                "new_password": "Password@1",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_reset_password_invalid(self) -> None:
        """유효하지 않은 비밀번호 요청"""
        serializer = ResetPasswordRequestSerializer(
            data={
                "email_token": "fnsfndslknfskl",
                "new_password": "invalid",
            }
        )
        self.assertFalse(serializer.is_valid())

    def test_reset_password_without_token(self) -> None:
        """이메일 토큰 누락 요청"""
        serializer = ResetPasswordRequestSerializer(
            data={
                "new_password": "Password@1",
            }
        )

        self.assertFalse(serializer.is_valid())

    def test_reset_password_without_password(self) -> None:
        """비밀번호 누락 요청"""
        serializer = ResetPasswordRequestSerializer(
            data={
                "email_token": "fnjksnfdkjnjk",
            }
        )
        self.assertFalse(serializer.is_valid())
