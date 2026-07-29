from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.follows.models.models import Follows
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
        self.url = reverse("posts:post_list_create")
        self.data = {
            "title": "test_title",
            "description": "test_description",
            "thumbnail": "local/upload/image/post/thumbnail/01JZWK7R2MNBX5QD8FHYC3VT9E.jpg",
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
                            "key": "local/upload/image/post/01JZWK7R2MNBX5QD8FHYC3VT9E.jpg",
                            "width": 1080,
                            "height": 1350,
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


class PostListViewTest(APITestCase):
    """PostListCreateView.get — root path(/api/v1/posts)의 팔로잉 피드 조회 테스트.

    /main 별칭과 동일한 서비스를 타므로 test_main_list_view.py와 같은 시나리오를
    root 경로에 대해서도 검증한다 (URL name만 다름, 회귀 시 어느 한쪽만 깨질 수 있음).
    """

    user: User
    author: User
    url: str

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.author = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        Follows.objects.create(follower=self.user, following=self.author)
        Post.objects.create(
            user=self.author,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.url = reverse("posts:post_list_create")

    def test_get_list_view(self) -> None:
        """로그인한 유저의 팔로잉 피드 조회(root 경로) 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    def test_fail_get_list_view_unauthenticated(self) -> None:
        """로그인 하지 않은 유저의 팔로잉 피드 조회(root 경로) 실패 테스트"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
