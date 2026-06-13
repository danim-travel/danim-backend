from datetime import date

from django.urls import reverse
from rest_framework.test import APITestCase

from apps.follows.models import Follows
from apps.users.models import User


class FollowerViewTest(APITestCase):
    target: User
    follower_a: User
    follower_b: User
    me: User

    @classmethod
    def setUpTestData(cls):
        def make_user(num):
            return User.objects.create_user(
                email=f"user{num}@example.com",
                password="Password@1",
                nickname=f"nick{num}",
                name=f"name{num}",
                birth_day=date(1990, 1, 1),
            )

        cls.target = make_user(1)
        cls.follower_a = make_user(2)
        cls.follower_b = make_user(3)
        cls.me = make_user(4)

        Follows.objects.create(follower=cls.follower_a, following=cls.target)
        Follows.objects.create(follower=cls.follower_b, following=cls.target)

    def _url(self, user_id):
        return reverse("users:followers", args=[user_id])

    def test_get_followers_success(self):
        """로그인 유저가 특정 유저의 팔로워 목록 조회 (200)"""
        self.client.force_authenticate(user=self.me)
        response = self.client.get(self._url(self.target.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("user_id", response.data["results"][0])
        self.assertIn("is_following", response.data["results"][0])

    def test_unauthenticated_returns_401(self):
        """비로그인 요청 시 401"""
        response = self.client.get(self._url(self.target.id))
        self.assertEqual(response.status_code, 401)

    def test_nonexistent_user_returns_404(self):
        """존재하지 않는 user_id → 404"""
        self.client.force_authenticate(user=self.me)
        response = self.client.get(self._url("01ZZZZZZZZZZZZZZZZZZZZZZZZ"))
        self.assertEqual(response.status_code, 404)
