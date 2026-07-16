from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.users.models import User
from apps.users.services.profile_service import ProfileService


class ProfileServiceTest(TestCase):

    service: ProfileService
    owner: User
    viewer: User
    stranger: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.service = ProfileService()

        cls.owner = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
        )
        cls.viewer = User.objects.create_user(
            email="viewer@example.com",
            password="Password@1",
            nickname="viewer_nick",
            name="viewer",
            birth_day=date(1991, 1, 1),
        )
        cls.stranger = User.objects.create_user(
            email="stranger@example.com",
            password="Password@1",
            nickname="stranger_nick",
            name="stranger",
            birth_day=date(1992, 1, 1),
        )
        followee = User.objects.create_user(
            email="followee@example.com",
            password="Password@1",
            nickname="followee_nick",
            name="followee",
            birth_day=date(1993, 1, 1),
        )

        # owner를 팔로우: viewer, stranger  → follower_count = 2
        Follows.objects.create(follower=cls.viewer, following=cls.owner)
        Follows.objects.create(follower=cls.stranger, following=cls.owner)
        # owner가 팔로우: followee           → following_count = 1
        Follows.objects.create(follower=cls.owner, following=followee)

        Post.objects.create(user=cls.owner, title="t1")
        Post.objects.create(user=cls.owner, title="t2")

    def test_get_profile_annotations(self) -> None:
        """annotate된 카운트/팔로우 방향이 정확한지"""
        user = self.service.get_profile(user_id=self.owner.id, request_user=self.viewer)
        self.assertEqual(user.follower_count, 2)  # type: ignore[attr-defined]
        self.assertEqual(user.following_count, 1)  # type: ignore[attr-defined]
        self.assertEqual(user.posts_count, 2)  # type: ignore[attr-defined]
        self.assertTrue(user.is_following)  # type: ignore[attr-defined]

    def test_get_profile_is_following_false(self) -> None:
        """owner를 팔로우하지 않은 followee 본인이 봐도 is_following=False"""
        # owner가 팔로우하는 followee를 request_user로 → followee는 owner를 팔로우 안 함
        followee = User.objects.get(email="followee@example.com")
        user = self.service.get_profile(user_id=self.owner.id, request_user=followee)
        self.assertFalse(user.is_following)  # type: ignore[attr-defined]

    def test_get_profile_not_found(self) -> None:
        """존재하지 않는 user_id → NotFoundException"""
        with self.assertRaises(NotFoundException):
            self.service.get_profile(
                user_id="01ZZZZZZZZZZZZZZZZZZZZZZZZ",
                request_user=self.viewer,
            )


class ProfilePostsPreviewLimitTest(TestCase):
    """프로필 게시글 미리보기 상한 — 무제한 직렬화(DoS 벡터) 회귀 방지."""

    def test_posts_preview_is_capped_and_latest_first(self) -> None:
        from apps.users.serializers.profile_serializer import (
            PROFILE_POSTS_PREVIEW_LIMIT,
            ProfileResponseSerializer,
        )

        owner = User.objects.create_user(
            email="heavy@example.com",
            password="Password@1",
            nickname="heavy_nick",
            name="heavy",
            birth_day=date(1990, 1, 1),
        )
        viewer = User.objects.create_user(
            email="viewer2@example.com",
            password="Password@1",
            nickname="viewer2_nick",
            name="viewer2",
            birth_day=date(1991, 1, 1),
        )
        total = PROFILE_POSTS_PREVIEW_LIMIT + 3
        posts = [Post.objects.create(user=owner, title=f"t{i}") for i in range(total)]

        user = ProfileService().get_profile(user_id=owner.id, request_user=viewer)
        data = ProfileResponseSerializer(user).data

        # 미리보기는 상한까지만, 총 개수는 posts_count로 전달
        self.assertEqual(len(data["posts"]), PROFILE_POSTS_PREVIEW_LIMIT)
        self.assertEqual(data["posts_count"], total)
        # 최신(-id) 순 유지 — 가장 최근 글이 첫 번째
        self.assertEqual(data["posts"][0]["post_id"], posts[-1].id)
