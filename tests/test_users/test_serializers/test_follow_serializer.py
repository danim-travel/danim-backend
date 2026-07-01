from apps.follows.models import Follows
from apps.users.models import User
from apps.users.serializers.follow_serializer import FollowerResponseSerializer
from tests.test_core.bases.user_base import UserBase


class FollowerResponseSerializerTest(UserBase):
    user1: User
    user2: User
    user3: User
    follow: Follows

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.follow = Follows.objects.create(follower=cls.user2, following=cls.user1)
        cls.follow.is_following = True

    def test_follow_response(self) -> None:

        serializer = FollowerResponseSerializer(
            self.follow,
        )
        data = serializer.data
        self.assertEqual(data["user_id"], self.user2.id)
        self.assertEqual(data["nickname"], self.user2.nickname)
        self.assertTrue(data["is_following"])
