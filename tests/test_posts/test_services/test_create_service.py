from datetime import date
from typing import Any

from django.test import TestCase

from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.posts.services.post_service import PostService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostCreateServiceTest(TestCase):

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
        self.data: dict[str, Any] = {
            "title": "test_title",
            "description": "test_description",
            "thumbnail": "prod/posts/thumbnail/uuid.jpg",
            "thumbnail_width": 1080,
            "thumbnail_height": 1350,
            "spots": [
                {
                    "order": 1,
                    "content": "test_content",
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
            ],
        }

    def test_create_post_service(self) -> None:
        """게시글 생성 성공 테스트"""
        post = self.service.create_post(self.data, self.user)
        self.assertIsInstance(post, Post)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Location.objects.count(), 1)
        self.assertEqual(PostSpot.objects.count(), 1)
        self.assertEqual(PostSpotImage.objects.count(), 1)
        self.assertEqual(post.title, "test_title")
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.thumbnail_width, 1080)
        self.assertEqual(post.thumbnail_height, 1350)
        post.refresh_from_db()
        self.assertEqual(post.spot_count, 1)

    def test_create_post_service_no_spots(self) -> None:
        """spots 없이 게시글 생성 성공 테스트"""
        data = {**self.data, "spots": []}
        post = self.service.create_post(data, self.user)
        self.assertIsInstance(post, Post)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(PostSpot.objects.count(), 0)
        post.refresh_from_db()
        self.assertEqual(post.spot_count, 0)

    def test_create_post_service_multiple_spots_and_images(self) -> None:
        """spot·이미지가 여러 개일 때 spot_count와 img_order가 정확한지 테스트"""
        spot = self.data["spots"][0]
        data = {
            **self.data,
            "spots": [
                {**spot, "order": 1},
                {**spot, "order": 2, "images": [*spot["images"], *spot["images"]]},
            ],
        }
        post = self.service.create_post(data, self.user)
        self.assertEqual(PostSpot.objects.count(), 2)
        self.assertEqual(PostSpotImage.objects.count(), 3)
        post.refresh_from_db()
        self.assertEqual(post.spot_count, 2)

        first_spot, second_spot = PostSpot.objects.order_by("order")
        self.assertEqual(list(first_spot.images.values_list("img_order", flat=True)), [1])
        self.assertEqual(
            list(
                second_spot.images.order_by("img_order").values_list(
                    "img_order", flat=True
                )
            ),
            [1, 2],
        )
        # bulk_create가 auto_now_add(created_at)를 정상적으로 채우는지 확인
        for image in PostSpotImage.objects.all():
            self.assertIsNotNone(image.created_at)
