from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.posts.serializers.main_list_serializer import PostMainListSerializer
from apps.posts.services.main_list_service import PostMainListService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostMainListSerializerTest(TestCase):

    service: PostMainListService
    user: User
    author: User
    post: Post

    def setUp(self) -> None:
        self.service = PostMainListService()
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
        self.post = Post.objects.create(
            user=self.author,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )

    @patch("apps.posts.serializers.main_list_serializer.s3_svc.create_img_url")
    def test_main_list_serializer(self, mock_s3) -> None:
        """게시글 메인 리스트 serializer 성공 테스트"""
        mock_s3.return_value = "https://s3.example.com/prod/posts/thumbnail/uuid.jpg"
        queryset = self.service.get_main_list(self.user)
        serializer = PostMainListSerializer(queryset, many=True)
        data = serializer.data

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["user"]["user_id"], self.author.id)
        self.assertEqual(data[0]["user"]["nickname"], self.author.nickname)
        self.assertEqual(data[0]["post"]["post_id"], self.post.id)
        self.assertEqual(data[0]["post"]["description"], self.post.description)
        self.assertEqual(data[0]["spots"], [])
        self.assertEqual(data[0]["spot_count"], 0)
        self.assertEqual(data[0]["comment_count"], 0)
        self.assertEqual(data[0]["like_count"], 0)
        self.assertFalse(data[0]["is_liked"])
        self.assertFalse(data[0]["is_bookmarked"])
