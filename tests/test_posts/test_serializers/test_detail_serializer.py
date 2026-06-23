from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.posts.models import Post, PostLike, PostSpot
from apps.posts.models.bookmark_model import BookMark
from apps.posts.serializers.detail_serializer import PostDetailSerializer
from apps.posts.services.detail_service import PostDetailService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostDetailSerializerTest(TestCase):

    service: PostDetailService
    user: User
    post: Post

    def setUp(self) -> None:
        self.service = PostDetailService()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )

    @patch("apps.posts.serializers.detail_serializer.s3_svc.create_img_url")
    def test_detail_serializer(self, mock_s3) -> None:
        """게시글 상세 조회 serializer 성공 테스트"""
        mock_s3.return_value = "https://s3.example.com/prod/posts/thumbnail/uuid.jpg"
        post = self.service.get_post_detail(self.post.id, self.user)
        serializer = PostDetailSerializer(post)
        data = serializer.data

        self.assertEqual(data["post"]["post_id"], self.post.id)
        self.assertEqual(data["post"]["title"], self.post.title)
        self.assertEqual(data["post"]["description"], self.post.description)
        self.assertEqual(data["user"]["user_id"], self.user.id)
        self.assertEqual(data["user"]["nickname"], self.user.nickname)
        self.assertEqual(data["spots"], [])
        self.assertEqual(data["like_count"], 0)
        self.assertEqual(data["comment_count"], 0)
        self.assertFalse(data["is_liked"])
        self.assertFalse(data["is_bookmarked"])
        self.assertTrue(data["is_owner"])
