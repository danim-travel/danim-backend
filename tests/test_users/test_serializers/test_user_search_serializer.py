from apps.users.models import User
from apps.users.serializers.user_search_serializer import UserSearchResponseSerializer
from tests.test_core.bases.user_base import UserBase


class UserSearchSerializerTest(UserBase):
    user: User

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_search_users_serializer(self) -> None:
        serializer = UserSearchResponseSerializer(self.user1)
        data = serializer.data

        self.assertEqual(data["user_id"], self.user1.id)
        self.assertEqual(data["nickname"], self.user1.nickname)
        assert self.user1.profile_img is not None
        self.assertIn(self.user1.profile_img, data["profile_img"])
        self.assertIn("X-Amz-Signature", data["profile_img"])


#
