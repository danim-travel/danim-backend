from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Location, Post, PostSpot
from apps.posts.services.post_service import PostService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostDeleteServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = PostService()
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            name="other",
            nickname="other_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )

    def test_delete_post(self) -> None:
        """게시글 삭제 성공 테스트"""
        self.service.delete_post(self.post.id, self.user)
        self.assertEqual(Post.objects.count(), 0)

    def test_delete_post_cleans_up_orphaned_locations(self) -> None:
        """게시글 삭제 시 spot이 쓰던 Location도 고아로 남지 않고 정리되는지 테스트"""
        location = Location.objects.create(
            address_name="test_address",
            road_address_name="test_road",
            place_name="test_place",
            x="127.0",
            y="37.0",
        )
        PostSpot.objects.create(post=self.post, location=location, order=1)
        self.service.delete_post(self.post.id, self.user)
        self.assertEqual(Location.objects.count(), 0)

    def test_fail_delete_post_not_found(self) -> None:
        """존재하지 않는 게시글 삭제 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.delete_post("nonexistent_id", self.user)

    def test_fail_delete_post_not_owner(self) -> None:
        """본인 게시글이 아닐 시 404 테스트 (존재 여부를 노출하지 않음)"""
        with self.assertRaises(NotFoundException):
            self.service.delete_post(self.post.id, self.other_user)
