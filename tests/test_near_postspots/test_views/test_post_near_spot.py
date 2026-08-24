from rest_framework import status
from rest_framework.test import APIClient

from apps.posts.models import Post
from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestNearPostSpotView(NearPostSpotBase):

    def setUp(self):
        self.client = APIClient()
        self.post_url = "/api/v1/posts/nearspots/post"

    def test_near_post_spot(self):
        """게시글 주변 게시글 조회 view 테스트 (base의 두 스팟은 약 1.1km 거리)"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.post_url, {"post_id": self.post_user1.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["post_id"], self.post_user1.id)
        near_group = response.data["near_spots"][0]
        self.assertEqual(near_group["spot_id"], self.postspot_user1.id)

        near_post_ids = [item["post_id"] for item in near_group["top_near"]]
        self.assertIn(self.post_user2.id, near_post_ids)

    def test_no_spots_for_post(self):
        """게시글에 스팟이 없으면 빈 near_spots를 반환한다"""
        empty_post = Post.objects.create(user=self.user1, title="empty")
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.post_url, {"post_id": empty_post.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"post_id": empty_post.id, "near_spots": []})

    def test_unauthenticated_user(self):
        """비로그인 유저는 401을 응답받는다"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.post_url, {"post_id": self.post_user1.id})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
