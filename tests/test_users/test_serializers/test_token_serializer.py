from django.test import TestCase

from apps.users.serializers.token_serializer import (
    TokenRequestSerializer,
    TokenResponseSerializer,
)


class TokenRequestSerializerTest(TestCase):

    def test_token_request(self) -> None:
        """jwt 요청 serializer test"""

        serializer = TokenRequestSerializer(
            data={
                "refresh_token": "test_refresh_token",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_token_request_missing_refresh_token(self) -> None:
        """refresh_token 누락"""
        serializer = TokenRequestSerializer(data={})
        self.assertFalse(serializer.is_valid())


class TokenResponseSerializerTest(TestCase):
    """jwt 응답 serializer test"""

    def test_token_response(self) -> None:
        serializer = TokenResponseSerializer(
            {
                "access_token": "test_access_token",
            }
        )
        self.assertEqual(serializer.data["access_token"], "test_access_token")
