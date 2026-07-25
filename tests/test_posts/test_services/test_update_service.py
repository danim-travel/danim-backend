from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.posts.services.post_service import PostService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostUpdateServiceTest(TestCase):

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
        self.spot_data = {
            "order": 1,
            "content": "new_content",
            "location": {
                "place_name": "성산일출봉",
                "address_name": "제주특별자치도 서귀포시 성산읍 성산리 1",
                "road_address_name": "제주특별자치도 서귀포시 성산읍 일출로 284-12",
                "x": "126.942492",
                "y": "33.458421",
            },
            "images": [
                {
                    "original_img": "제주도1일차.png",
                    "key": "prod/posts/uuid.jpg",
                    "width": 1080,
                    "height": 1350,
                }
            ],
        }

    def test_update_post_title(self) -> None:
        """title만 수정 성공 테스트"""
        self.service.update_post(self.post.id, {"title": "new_title"}, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "new_title")

    def test_update_post_description(self) -> None:
        """description만 수정 성공 테스트"""
        self.service.update_post(
            self.post.id, {"description": "new_description"}, self.user
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.description, "new_description")

    def test_update_post_spots(self) -> None:
        """spots 수정 시 기존 spots 삭제 후 재생성 테스트"""
        self.service.update_post(self.post.id, {"spots": [self.spot_data]}, self.user)
        self.assertEqual(PostSpot.objects.filter(post=self.post).count(), 1)
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(PostSpotImage.objects.count(), 1)

    def test_update_post_spots_replaces_existing(self) -> None:
        """spots 수정 시 기존 spots 교체 테스트"""
        location = Location.objects.create(
            address_name="old_address",
            road_address_name="old_road",
            place_name="old_place",
            x="127.0",
            y="37.0",
        )
        PostSpot.objects.create(post=self.post, location=location, order=1)
        self.service.update_post(self.post.id, {"spots": [self.spot_data]}, self.user)
        self.assertEqual(PostSpot.objects.filter(post=self.post).count(), 1)

    def test_fail_update_post_not_found(self) -> None:
        """존재하지 않는 게시글 수정 시 404 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.update_post("nonexistent_id", {"title": "new_title"}, self.user)

    def test_fail_update_post_not_owner(self) -> None:
        """본인 게시글이 아닐 시 404 테스트 (존재 여부를 노출하지 않음)"""
        with self.assertRaises(NotFoundException):
            self.service.update_post(
                self.post.id, {"title": "new_title"}, self.other_user
            )
