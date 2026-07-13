from rest_framework import status
from rest_framework.test import APIClient

from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestNearUserSpotView(NearPostSpotBase):

    def setUp(self):
        self.client = APIClient()

    def test_user_near_spot_none_post(self):
        """주변 게시글이 하나도 없을떄 view 테스트"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"latitude": 37.4, "longitude": 127.0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["top_near"], [])

    def test_user_near_spot(self):
        """주변 게시글 있을때 view 테스트"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {"latitude": 37.338, "longitude": 127.0})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["top_near"]), 2)
        first = response.data["top_near"][0]
        self.assertIn("post_id", first)
        self.assertIn("place_name", first)
        self.assertEqual(first["x"], "127.00000000000000")

    def test_unauthered_user_near_spot(self):
        """비로그인한 유저의 주변게시글 조회 view 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {"latitude": 37.338, "longitude": 127.0})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
