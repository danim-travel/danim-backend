from django.test import TestCase

from apps.users.serializers.check_nickname_serializer import CheckNicknameSerializer


class CheckNicknameSerializerTest(TestCase):

    def test_check_nickname_valid(self) -> None:
        """유효한 nickname"""
        serializer = CheckNicknameSerializer(data={"nickname": "test_nickname"})
        self.assertTrue(serializer.is_valid())

    def test_check_nickname_invalid(self) -> None:
        """유효하지 않은 nickname"""
        serializer = CheckNicknameSerializer(data={"nickname": "테스트_닉네임"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)
