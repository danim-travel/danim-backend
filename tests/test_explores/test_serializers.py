from datetime import date

from django.test import TestCase

from apps.explores.serializers import (
    ExploreFeedsSerializer,
    ExploreQuerySerializer,
    ExploreResponseSerializer,
)
from apps.posts.models import Post
from apps.users.models import LoginType, User
from tests.test_explores.utils import user_and_post


class ExploreSerializerTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user, cls.post = user_and_post()
        cls.instance = {
            "id": cls.post.id,
            "thumbnail": cls.post.thumbnail,
            "like_count": cls.post.like_count,
            "comment_count": cls.post.comment_count,
        }
        cls.ser = ExploreFeedsSerializer(instance=cls.instance)

    def test_page_size_always_10(self):
        ser = ExploreQuerySerializer(data={"page_size": 20})
        ser.is_valid()
        self.assertEqual(ser.validated_data["page_size"], 10)

    def test_query_ser(self):
        ser = ExploreQuerySerializer(data={})
        ser.is_valid()
        self.assertEqual(ser.validated_data["page_size"], 10)
        self.assertEqual(ser.validated_data["search"], None)
        self.assertEqual(ser.validated_data["cursor"], None)
        self.assertEqual(ser.validated_data["seed"], None)

    def test_feeds_ser(self):
        self.assertEqual(self.ser.data["post_id"], self.post.id)
        self.assertEqual(self.ser.data["thumbnail"], self.post.thumbnail)
        self.assertEqual(self.ser.data["like_count"], self.post.like_count)
        self.assertEqual(self.ser.data["comment_count"], self.post.comment_count)

    def test_response_ser(self):
        ser = ExploreResponseSerializer(
            {
                "next": "https://api.example.com/explores/?cursor=abc",
                "seed": 42,
                "results": [self.instance],
            }
        )
        self.assertEqual(ser.data["next"], "https://api.example.com/explores/?cursor=abc")
        self.assertEqual(ser.data["seed"], 42)
        self.assertEqual(
            ser.data["results"],
            [
                {
                    "post_id": self.post.id,
                    "thumbnail": self.post.thumbnail,
                    "like_count": self.post.like_count,
                    "comment_count": self.post.comment_count,
                }
            ],
        )
