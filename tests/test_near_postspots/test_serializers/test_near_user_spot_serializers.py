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

    def test_request_serializer_fail_latitude_out_of_range(self):
        """위도가 -90~90 범위를 벗어나면 검증에 실패한다"""
        request_data = {"latitude": "91", "longitude": "127.0"}
        serializer = NearUserQuerySerializer(data=request_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_serializer_fail_longitude_out_of_range(self):
        """경도가 -180~180 범위를 벗어나면 검증에 실패한다"""
        request_data = {"latitude": "37.0", "longitude": "200"}
        serializer = NearUserQuerySerializer(data=request_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_serializer_fail_latitude_infinite(self):
        """위도가 무한대(inf)이면 검증에 실패한다"""
        request_data = {"latitude": "inf", "longitude": "127.0"}
        serializer = NearUserQuerySerializer(data=request_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_serializer_fail_latitude_nan(self):
        """위도가 NaN이면 검증에 실패한다 (min/max 범위 비교로는 걸러지지 않음)"""
        request_data = {"latitude": "nan", "longitude": "127.0"}
        serializer = NearUserQuerySerializer(data=request_data)
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_request_serializer_boundary_values_valid(self):
        """위도/경도 경계값(±90, ±180)은 유효한 값으로 통과한다"""
        request_data = {"latitude": "90", "longitude": "180"}
        serializer = NearUserQuerySerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["latitude"], 90.0)
        self.assertEqual(serializer.validated_data["longitude"], 180.0)


class TestNearUserSpotResponseSerializer(NearPostSpotBase):

    def setUp(self):
        super().setUp()
        self.postspot_user1.distance = 1.2
        self.postspot_user2.distance = 1.2

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
