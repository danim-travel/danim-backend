from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.users.models import User


class ProfileViewTest(APITestCase):

    owner: User
    viewer: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            intro="여행을 좋아하는 사람입니다.",
            birth_day=date(1990, 1, 1),
            profile_img="profile_key",
        )
        cls.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="Password@1",
            nickname="viewer_nick",
            name="viewer",
            birth_day=date(1991, 1, 1),
        )
        follower2 = User.objects.create_user(
            email="f2@example.com",
            password="Password@1",
            nickname="f2_nick",
            name="f2",
            birth_day=date(1992, 1, 1),
        )
        followee = User.objects.create_user(
            email="followee@example.com",
            password="Password@1",
            nickname="followee_nick",
            name="followee",
            birth_day=date(1993, 1, 1),
        )
        # owner를 팔로우: viewer, follower2 → follower 2 / owner가 팔로우: followee → following 1
        Follows.objects.create(follower=cls.viewer, following=cls.owner)
        Follows.objects.create(follower=follower2, following=cls.owner)
        Follows.objects.create(follower=cls.owner, following=followee)
        Post.objects.create(user=cls.owner, title="t1")

    def _url(self, user_id: str) -> str:
        return reverse("users:profile", kwargs={"user_id": user_id})

    @patch("apps.core.storage.s3.services.s3_svc.create_download_presigned_url")
    def test_profile_success(self, mock_create_download_presigned_url) -> None:
        """프로필 조회 성공 (200) 및 응답 필드 검증"""
        mock_create_download_presigned_url.return_value = "https://s3.example.com/img.png"
        self.client.force_authenticate(user=self.viewer)

        response = self.client.get(self._url(self.owner.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "owner_nick")
        self.assertEqual(response.data["intro"], "여행을 좋아하는 사람입니다.")
        self.assertEqual(response.data["profile_img"], "https://s3.example.com/img.png")
        self.assertEqual(response.data["follower"], 2)
        self.assertEqual(response.data["following"], 1)
        self.assertTrue(response.data["is_following"])
        self.assertEqual(response.data["posts_count"], 1)
        self.assertEqual(len(response.data["posts"]), 1)

    def test_profile_not_found(self) -> None:
        """존재하지 않는 user_id → 404"""
        self.client.force_authenticate(user=self.viewer)
        response = self.client.get(self._url("01ZZZZZZZZZZZZZZZZZZZZZZZZ"))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_profile_unauthenticated(self) -> None:
        """인증 없이 요청 시 401"""
        response = self.client.get(self._url(self.owner.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
