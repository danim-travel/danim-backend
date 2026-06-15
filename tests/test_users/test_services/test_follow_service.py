from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models import Follows
from apps.users.models import User
from apps.users.services.follow_service import FollowService


class FollowServiceTest(TestCase):
    service: FollowService
    target: User
    follower_a: User
    follower_b: User
    me: User

    @classmethod
    def setUpTestData(cls):
        cls.service = FollowService()

        def make_user(num):
            return User.objects.create_user(
                email=f"user{num}@example.com",
                password="Password@1",
                nickname=f"nick{num}",
                name=f"name{num}",
                birth_day=date(1990, 1, 1),
            )

        cls.target = make_user(1)  # 팔로워 목록의 주인
        cls.follower_a = make_user(2)  # target을 팔로우
        cls.follower_b = make_user(3)  # target을 팔로우
        cls.me = make_user(4)  # 요청자

        # follower_a, follower_b → target 팔로우
        Follows.objects.create(follower=cls.follower_a, following=cls.target)
        Follows.objects.create(follower=cls.follower_b, following=cls.target)
        # me → follower_a 팔로우 (follower_b는 안 함)
        Follows.objects.create(follower=cls.me, following=cls.follower_a)

    def test_get_follower_returns_followers(self):
        """target의 팔로워들을 반환 (target을 팔로우하는 사람들)"""
        qs = self.service.get_follower(self.target.id, self.me)

        self.assertEqual(qs.count(), 2)
        follower_ids = {f.follower_id for f in qs}
        self.assertEqual(follower_ids, {self.follower_a.id, self.follower_b.id})

    def test_is_following_annotation(self):
        """is_following: 요청자(me)가 각 팔로워를 팔로우하는지"""
        qs = self.service.get_follower(self.target.id, self.me)
        by_id = {f.follower_id: f.is_following for f in qs}

        self.assertTrue(by_id[self.follower_a.id])  # me가 follower_a 팔로우
        self.assertFalse(by_id[self.follower_b.id])  # me가 follower_b 안 함

    def test_nonexistent_user_raises_not_found(self):
        """없는 user_id → NotFoundException"""
        with self.assertRaises(NotFoundException):
            self.service.get_follower("01ZZZZZZZZZZZZZZZZZZZZZZZZ", self.me)
