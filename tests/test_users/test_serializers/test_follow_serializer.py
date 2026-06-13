from datetime import date

from django.test import TestCase

from apps.follows.models import Follows
from apps.users.models import User
from apps.users.serializers.follow_serializer import FollowerResponseSerializer


class FollowerResponseSerializerTest(TestCase):
    user1: User
    user2: User
    user3: User
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

        # 프로필 이미지가 None인 유저
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
        )

        # 소개글이 None인 유저
        cls.user3 = User.objects.create_user(
            email="test3@example.com",
            password="Password@1",
            nickname="test3",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
        )
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
