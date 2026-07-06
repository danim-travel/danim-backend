from apps.core.exceptions.exception import NotFoundException
from apps.follows.models import Follows
from apps.users.models import User
from apps.users.services.follow_service import FollowService
from tests.test_core.bases.user_base import UserBase


class FollowingServiceTest(UserBase):
    service: FollowService
    target: User
    followee_a: User
    followee_b: User
    me: User

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.service = FollowService()

        cls.target = cls.user1  # 팔로잉 목록의 주인
        cls.followee_a = cls.user2  # target이 팔로우하는 사람
        cls.followee_b = cls.user3  # target이 팔로우하는 사람
        cls.me = cls.social_user  # 요청자

        # target → followee_a, followee_b 팔로우
        Follows.objects.create(follower=cls.target, following=cls.followee_a)
        Follows.objects.create(follower=cls.target, following=cls.followee_b)
        # me → followee_a 팔로우 (followee_b는 안 함)
        Follows.objects.create(follower=cls.me, following=cls.followee_a)

    def test_get_following_returns_followings(self):
        """target의 팔로잉들을 반환 (target이 팔로우하는 사람들)"""
        qs = self.service.get_following(self.target.id, self.me)

        self.assertEqual(qs.count(), 2)
        following_ids = {f.following_id for f in qs}
        self.assertEqual(following_ids, {self.followee_a.id, self.followee_b.id})

    def test_is_following_annotation(self):
        """is_following: 요청자(me)가 각 팔로잉 유저를 팔로우하는지"""
        qs = self.service.get_following(self.target.id, self.me)
        by_id = {f.following_id: f.is_following for f in qs}

        self.assertTrue(by_id[self.followee_a.id])  # me가 followee_a 팔로우
        self.assertFalse(by_id[self.followee_b.id])  # me가 followee_b 안 함

    def test_nonexistent_user_raises_not_found(self):
        """없는 user_id → NotFoundException"""
        with self.assertRaises(NotFoundException):
            self.service.get_following("01ZZZZZZZZZZZZZZZZZZZZZZZZ", self.me)
