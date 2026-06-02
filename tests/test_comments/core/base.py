from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.comments.models import Comment, CommentLike
from apps.posts.models import Post
from apps.users.models.models import LoginType, User


class CommentBaseTest(TestCase):
    client: APIClient
    user: User
    post: Post
    comment_content: Comment
    comment_image: Comment
    comment_like: CommentLike
    data_for_content: dict
    data_for_img: dict
    data_fail_content: dict
    data_fail_img: dict
    data_for_comment_content: dict
    data_for_comment_img: dict
    fail_data_for_comment_content: dict
    fail_data_for_none_post: dict
    fail_data_for_only_post: dict
    url: str

    def setUp(self):

        self.client = APIClient()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day=date(1970, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            title="test_title",
            content="test",
            user=self.user,
        )
        self.comment_content = Comment.objects.create(
            post=self.post,
            user=self.user,
            content="test_1",
            img_key=None,
            original_img=None,
        )
        self.comment_image = Comment.objects.create(
            user=self.user,
            post=self.post,
            content=None,
            img_key="dev/comments/uuid.png",
            original_img="uuid.png",
        )
        self.comment_like = CommentLike.objects.create(
            user=self.user,
            comment=self.comment_content,
        )
        self.data_for_content = {"post_id": self.post.id, "content": "test_content"}
        self.data_for_img = {
            "post_id": self.post.id,
            "comment_img": {"key": "prod/.../AXd399...png", "original_img": "dog.png"},
        }
        self.fail_data_for_content = {"post_id": self.post.id, "content": "a" * 101}
        self.fail_data_for_img = {
            "post_id": self.post.id,
            "comment_img": {"key": "p" * 256, "original_img": "d" * 101},
        }
        self.fail_data_for_none_post = {
            "post_id": "없는 게시글 아이디",
            "content": "test_content",
        }
        self.fail_data_for_only_post = {
            "post_id": self.post.id,
        }
        self.url = "/api/v1/comments/"
