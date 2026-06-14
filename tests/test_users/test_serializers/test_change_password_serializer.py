from django.test import TestCase

from apps.users.serializers.change_password_serializer import (
    ChangePasswordRequestSerializer,
)


class ChangePasswordSerializerTest(TestCase):

    def test_change_password(self) -> None:
        serializer = ChangePasswordRequestSerializer(
            data={
                "password": "Password@1",
                "new_password": "Password@2",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_change_password_invalid_new_password(self) -> None:
        serializer = ChangePasswordRequestSerializer(
            data={
                "password": "Password@1",
                "new_password": "weak",
            }
        )
        self.assertFalse(serializer.is_valid())
