from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType


class PostCreateViewTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.url = reverse("posts:post_create")
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

    def test_create_post_view(self) -> None:
        """로그인한 유저의 게시글 생성 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)

    def test_fail_create_post_view_unauthenticated(self) -> None:
        """로그인 하지 않은 유저의 게시글 생성 실패 테스트"""
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Post.objects.count(), 0)
