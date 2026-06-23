from datetime import date

from django.test import TestCase

from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.posts.services.create_service import PostCreateService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostCreateServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = PostCreateService()
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.data = {
            "title": "test_title",
            "description": "test_description",
            "thumbnail": "prod/posts/thumbnail/uuid.jpg",
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

    def test_create_post_service_no_spots(self) -> None:
        """spots 없이 게시글 생성 성공 테스트"""
        data = {**self.data, "spots": []}
        post = self.service.create_post(data, self.user)
        self.assertIsInstance(post, Post)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(PostSpot.objects.count(), 0)
