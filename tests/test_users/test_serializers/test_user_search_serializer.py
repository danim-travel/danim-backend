from datetime import date

from django.test import TestCase

from apps.users.models import User
from apps.users.serializers.user_search_serializer import UserSearchResponseSerializer


class UserSearchSerializerTest(TestCase):
    user: User

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            birth_day=date(1970, 1, 1),
        )

    def test_search_users_serializer(self) -> None:
        serializer = UserSearchResponseSerializer(self.user)
        data = serializer.data

        self.assertEqual(data["user_id"], self.user.id)
        self.assertEqual(data["nickname"], self.user.nickname)
        self.assertIsNone(data["profile_img"])
