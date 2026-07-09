from django.test import TestCase
from rest_framework import serializers

from apps.posts.near_postspot.serializers import (
    NearUserQuerySerializer,
    NearUserResponseSerializer,
)
from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestNearUserSpotSerializer(TestCase):

    def test_request_serializer(self):
        """serializer float 정상변환확인"""
        request_data = {
            "latitude": "37.0",
            "longitude": "127.0",
        }
        serializer = NearUserQuerySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.validated_data["latitude"], float(request_data["latitude"])
        )
        self.assertEqual(
            serializer.validated_data["longitude"], float(request_data["longitude"])
        )

    def test_request_serializer_fail_none(self):
        """serializer 필드 누락 에러처리"""
        request_data_fail_none = {
            "latitude": "37.0",
        }
        serializer = NearUserQuerySerializer(data=request_data_fail_none)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_serializer_fail_str(self):
        """serializer float 형변환 힐패 에러처리"""
        request_data_fail_str = {
            "latitude": "37.0",
            "longitude": "float로 형변환 안되는 문자열",
        }
        serializer = NearUserQuerySerializer(data=request_data_fail_str)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestNearUserSpotResponseSerializer(NearPostSpotBase):

    def test_response_serializer(self):
        """serializer응답 테스트"""
        serializer = NearUserResponseSerializer({"top_near": [self.postspot_user1]})
        self.assertEqual(len(serializer.data), 1)
        spot_object = serializer.data["top_near"][0]
        self.assertEqual(spot_object["post_id"], self.postspot_user1.post_id)
        self.assertEqual(spot_object["thumbnail"], self.postspot_user1.post.thumbnail)
        self.assertEqual(spot_object["y"], str(self.postspot_user1.location.y))
        self.assertEqual(spot_object["x"], str(self.postspot_user1.location.x))
        self.assertEqual(
            spot_object["place_name"], self.postspot_user1.location.place_name
        )

    def test_response_serializer_multiple(self):
        """여러 게시글 직렬화"""
        serializer = NearUserResponseSerializer(
            {"top_near": [self.postspot_user1, self.postspot_user2]}
        )
        self.assertEqual(len(serializer.data["top_near"]), 2)

    def test_response_serializer_empty(self):
        """주변 게시글 없을 때 빈 top_near"""
        serializer = NearUserResponseSerializer({"top_near": []})
        self.assertEqual(serializer.data["top_near"], [])
