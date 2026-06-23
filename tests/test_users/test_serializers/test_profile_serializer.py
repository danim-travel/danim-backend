from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.users.models import User
from apps.users.serializers.profile_serializer import ProfileResponseSerializer
from apps.users.services.profile_service import ProfileService


class ProfileResponseSerializerTest(TestCase):

    service: ProfileService
    owner: User
    viewer: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.service = ProfileService()

        # 프로필 주인(조회 대상)
        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            intro="여행을 좋아하는 사람입니다.",
            birth_day=date(1990, 1, 1),
            profile_img="profile_key",
        )
        # 조회 요청자(is_following 계산용)
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

        # owner를 팔로우하는 사람: viewer, follower2  → follower(나를 팔로우) = 2
        Follows.objects.create(follower=cls.viewer, following=cls.owner)
        Follows.objects.create(follower=follower2, following=cls.owner)
        # owner가 팔로우하는 사람: followee          → following(내가 팔로우) = 1
        Follows.objects.create(follower=cls.owner, following=followee)

        # owner의 게시글 2개 → posts_count = 2
        Post.objects.create(user=cls.owner, title="t1", description="d1")
        Post.objects.create(user=cls.owner, title="t2", description="d2")

    @patch("apps.core.storage.s3.services.s3_svc.create_download_presigned_url")
    def test_profile_serializer(self, mock_create_download_presigned_url) -> None:
        """프로필 조회 직렬화 성공 + 카운트/팔로우 방향 검증"""
        mock_create_download_presigned_url.return_value = "https://s3.example.com/img.png"

        user = self.service.get_profile(user_id=self.owner.id, request_user=self.viewer)
        data = ProfileResponseSerializer(user).data

        self.assertEqual(data["nickname"], "owner_nick")
        self.assertEqual(data["intro"], "여행을 좋아하는 사람입니다.")
        self.assertEqual(data["profile_img"], "https://s3.example.com/img.png")
        # related_name 반대 매핑 검증: 나를 팔로우(2) vs 내가 팔로우(1)
        self.assertEqual(data["follower"], 2)
        self.assertEqual(data["following"], 1)
        self.assertTrue(data["is_following"])  # viewer가 owner를 팔로우 중
        self.assertEqual(data["posts_count"], 2)
        self.assertEqual(data["posts"][0]["title"], "t2")
        self.assertEqual(data["posts"][1]["title"], "t1")
        self.assertEqual(len(data["posts"]), 2)

    @patch("apps.core.storage.s3.services.s3_svc.create_download_presigned_url")
    def test_is_following_false(self, mock_create_download_presigned_url) -> None:
        """owner를 팔로우하지 않은 유저가 조회하면 is_following=False"""
        mock_create_download_presigned_url.return_value = "https://s3.example.com/img.png"

        stranger = User.objects.create_user(
            email="stranger@example.com",
            password="Password@1",
            nickname="stranger_nick",
            name="stranger",
            birth_day=date(1994, 1, 1),
        )
        user = self.service.get_profile(user_id=self.owner.id, request_user=stranger)
        data = ProfileResponseSerializer(user).data

        self.assertFalse(data["is_following"])

    @patch("apps.core.storage.s3.services.s3_svc.create_download_presigned_url")
    def test_profile_img_none(self, mock_create_download_presigned_url) -> None:
        """프로필 이미지가 없으면 profile_img는 None"""
        user = self.service.get_profile(user_id=self.viewer.id, request_user=self.owner)
        data = ProfileResponseSerializer(user).data

        self.assertIsNone(data["profile_img"])
        mock_create_download_presigned_url.assert_not_called()  # key 없으면 s3 호출 안 함
