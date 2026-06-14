from datetime import date

from django.test import TestCase

from apps.follows.models import Follows
from apps.users.models import User
from apps.users.serializers.follow_serializer import FollowingResponseSerializer


class FollowingResponseSerializerTest(TestCase):
    user1: User
    user2: User
    follow: Follows

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            intro="test_intro",
            birth_day=date(1970, 1, 1),
        )
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
        )
        # user1 → user2 팔로우 (user2가 user1의 팔로잉)
        cls.follow = Follows.objects.create(follower=cls.user1, following=cls.user2)
        cls.follow.is_following = True

    def test_following_response(self) -> None:
        serializer = FollowingResponseSerializer(self.follow)
        data = serializer.data

        self.assertEqual(data["user_id"], self.user2.id)  # following = user2
        self.assertEqual(data["nickname"], self.user2.nickname)
        self.assertIn("profile_img", data)
        self.assertTrue(data["is_following"])
