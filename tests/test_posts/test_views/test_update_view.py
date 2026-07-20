from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Post
from apps.users.models import User
from apps.users.models.models import LoginType


class PostUpdateViewTest(APITestCase):

    def setUp(self) -> None:
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create(
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
            thumbnail="local/upload/image/post/thumbnail/01JZWK7R2MNBX5QD8FHYC3VT9E.jpg",
        )
        self.url = reverse("posts:post_detail", kwargs={"post_id": self.post.id})
        self.data = {
            "title": "updated_title",
            "description": "updated_description",
            "thumbnail": "local/upload/image/post/thumbnail/01JZWK7R2MNBX5QD8FHYC3VT8D.jpg",
            "thumbnail_width": 1080,
            "thumbnail_height": 1350,
            "spots": [
                {
                    "order": 1,
                    "content": "updated_content",
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

    def test_update_post_view(self) -> None:
        """로그인한 유저의 게시글 수정 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "updated_title")

    def test_update_post_view_partial(self) -> None:
        """일부 필드만 수정 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {"title": "partial_update"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, "partial_update")

    def test_fail_update_post_view_unauthenticated(self) -> None:
        """비로그인 유저의 게시글 수정 시 401 테스트"""
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_fail_update_post_view_not_owner(self) -> None:
        """본인 게시글이 아닐 시 403 테스트"""
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(self.url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_fail_update_post_view_not_found(self) -> None:
        """존재하지 않는 게시글 수정 시 404 테스트"""
        self.client.force_authenticate(user=self.user)
        url = reverse("posts:post_detail", kwargs={"post_id": "nonexistent_id"})
        response = self.client.patch(url, self.data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_fail_update_post_view_no_fields(self) -> None:
        """아무 필드도 없을 시 400 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
