from django.test import TestCase

from apps.users.serializers.token_serializer import TokenResponseSerializer


class TokenResponseSerializerTest(TestCase):
    """jwt 응답 serializer test"""

    def test_token_response(self) -> None:
        serializer = TokenResponseSerializer(
            {
                "access_token": "test_access_token",
            }
        )
        self.assertEqual(serializer.data["access_token"], "test_access_token")
