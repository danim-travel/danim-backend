from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.posts.models import Post
from apps.posts.serializers.post_simple_serializer import PostSimpleSerializer
from apps.users.models import User


class PostSimpleSerializerTest(TestCase):

    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="author@example.com",
            password="Password@1",
            nickname="author_nick",
            name="author",
            birth_day=date(1990, 1, 1),
        )

    @patch("apps.core.storage.s3.services.s3_svc.create_img_url")
    def test_with_thumbnail(self, mock_create_img_url) -> None:
        """썸네일 key가 있으면 post_id/title/thumbnail(URL)로 직렬화"""
        mock_create_img_url.return_value = "https://s3.example.com/thumb.png"
        post = Post.objects.create(
            user=self.user, title="제주도 여행", thumbnail="thumb_key"
        )

        data = PostSimpleSerializer(post).data

        self.assertEqual(data["post_id"], post.id)
        self.assertEqual(data["title"], "제주도 여행")
        self.assertEqual(data["thumbnail"], "https://s3.example.com/thumb.png")
        mock_create_img_url.assert_called_once_with("thumb_key")

    @patch("apps.core.storage.s3.services.s3_svc.create_img_url")
    def test_without_thumbnail(self, mock_create_img_url) -> None:
        """썸네일이 없으면 thumbnail=None, s3 호출 안 함"""
        post = Post.objects.create(user=self.user, title="썸네일 없는 글")

        data = PostSimpleSerializer(post).data

        self.assertEqual(data["post_id"], post.id)
        self.assertEqual(data["title"], "썸네일 없는 글")
        self.assertIsNone(data["thumbnail"])
        mock_create_img_url.assert_not_called()

    @patch("apps.core.storage.s3.services.s3_svc.create_img_url")
    def test_many(self, mock_create_img_url) -> None:
        """many=True 로 여러 게시글 직렬화"""
        mock_create_img_url.return_value = "https://s3.example.com/thumb.png"
        Post.objects.create(user=self.user, title="t1", thumbnail="k1")
        Post.objects.create(user=self.user, title="t2", thumbnail="k2")

        data = PostSimpleSerializer(self.user.posts.all(), many=True).data

        self.assertEqual(len(data), 2)
        self.assertEqual({d["title"] for d in data}, {"t1", "t2"})
