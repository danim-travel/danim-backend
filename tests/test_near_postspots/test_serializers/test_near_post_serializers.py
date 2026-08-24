from django.test import TestCase
from rest_framework import serializers

from apps.posts.near_postspot.serializers import (
    NearPostQuerySerializer,
    NearPostResponseSerializer,
)
from tests.test_core.bases.near_postspot_base import NearPostSpotBase


class TestNearPostQuerySerializer(TestCase):

    def test_valid_post_id(self):
        """post_id가 있으면 정상 검증된다"""
        serializer = NearPostQuerySerializer(data={"post_id": "abc123"})
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data["post_id"], "abc123")

    def test_missing_post_id_fails(self):
        """post_id가 없으면 검증에 실패한다"""
        serializer = NearPostQuerySerializer(data={})
        with self.assertRaises(serializers.ValidationError):
            serializer.is_valid(raise_exception=True)


class TestNearPostResponseSerializer(NearPostSpotBase):

    def setUp(self):
        super().setUp()
        self.postspot_user1.distance = 0.5
        self.postspot_user2.distance = 1.5

    def test_serializes_nested_near_spots(self):
        """post_id -> near_spots(spot_id, top_near) 중첩 구조를 직렬화한다"""
        data = {
            "post_id": self.post_user1.id,
            "near_spots": [
                {"spot_id": self.postspot_user1.id, "top_near": [self.postspot_user2]},
            ],
        }
        serializer = NearPostResponseSerializer(data)

        self.assertEqual(serializer.data["post_id"], self.post_user1.id)
        group = serializer.data["near_spots"][0]
        self.assertEqual(group["spot_id"], self.postspot_user1.id)
        self.assertEqual(len(group["top_near"]), 1)
        self.assertEqual(group["top_near"][0]["post_id"], self.postspot_user2.post_id)

    def test_serializes_empty_near_spots(self):
        """near_spots가 빈 리스트여도 정상 직렬화된다"""
        data = {"post_id": self.post_user1.id, "near_spots": []}
        serializer = NearPostResponseSerializer(data)

        self.assertEqual(serializer.data["near_spots"], [])
