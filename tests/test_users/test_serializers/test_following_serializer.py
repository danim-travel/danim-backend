from apps.follows.models import Follows
from apps.users.serializers.follow_serializer import FollowingResponseSerializer
from tests.test_core.bases.user_base import UserBase


class FollowingResponseSerializerTest(UserBase):

    follow: Follows

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        # user1 → user2 팔로우 (user2가 user1의 팔로잉)
        cls.follow = Follows.objects.create(follower=cls.user1, following=cls.user2)

    def test_following_response(self) -> None:
        self.follow.is_following = True  # type: ignore[attr-defined]

        serializer = FollowingResponseSerializer(self.follow)
        data = serializer.data

        self.assertEqual(data["user_id"], self.user2.id)  # following = user2
        self.assertEqual(data["nickname"], self.user2.nickname)
        self.assertIn("profile_img", data)
        self.assertTrue(data["is_following"])
