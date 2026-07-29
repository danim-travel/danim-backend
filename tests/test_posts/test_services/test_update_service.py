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
        self.post.refresh_from_db()
        self.assertEqual(self.post.spot_count, 1)

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
        self.post.refresh_from_db()
        self.assertEqual(self.post.spot_count, 1)
        # 교체 후 이전 spot이 쓰던 Location은 고아가 되어 정리되어야 한다
        self.assertEqual(Location.objects.count(), 1)
        self.assertFalse(Location.objects.filter(address_name="old_address").exists())

    def test_update_post_spots_repeated_edits_do_not_accumulate_orphans(self) -> None:
        """동일 post를 여러 번 수정해도 Location 고아가 누적되지 않는지 테스트"""
        for _ in range(3):
            self.service.update_post(self.post.id, {"spots": [self.spot_data]}, self.user)
        self.assertEqual(Location.objects.count(), 1)

    def test_update_post_spots_multiple_spots_and_images(self) -> None:
        """spot·이미지가 여러 개일 때 spot_count와 img_order가 정확한지 테스트"""
        data = {
            "spots": [
                {**self.spot_data, "order": 1},
                {
                    **self.spot_data,
                    "order": 2,
                    "images": [*self.spot_data["images"], *self.spot_data["images"]],
                },
            ]
        }
        self.service.update_post(self.post.id, data, self.user)
        self.assertEqual(PostSpot.objects.filter(post=self.post).count(), 2)
        self.assertEqual(PostSpotImage.objects.count(), 3)
        self.post.refresh_from_db()
        self.assertEqual(self.post.spot_count, 2)

    def test_update_post_spots_empty_resets_spot_count(self) -> None:
        """spots를 빈 리스트로 수정 시 spot_count가 0으로 초기화되는지 테스트"""
        self.service.update_post(self.post.id, {"spots": [self.spot_data]}, self.user)
        self.service.update_post(self.post.id, {"spots": []}, self.user)
        self.assertEqual(PostSpot.objects.filter(post=self.post).count(), 0)
        self.post.refresh_from_db()
        self.assertEqual(self.post.spot_count, 0)

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
