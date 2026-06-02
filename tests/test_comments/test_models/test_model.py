from datetime import date

from django.test import TestCase

from apps.comments.models import Comment, CommentLike
from apps.posts.models import Post
from apps.users.models.models import LoginType, User


class CommentTest(TestCase):
    """comment와 comment_like 모델 테스트"""

    user: User
    comment_no_image: Comment
    comment_image: Comment
    comment_like: CommentLike

    def setUp(self):
        """Comment test를 위한 공통 데이터 생성 (user,post,comment)"""
        self.user = User.objects.create_user(
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
        self.comment_no_image = Comment.objects.create(
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
            comment=self.comment_no_image,
        )

    def test_create_comment_no_image(self) -> None:
        """이미지 없는 댓글 생성 성공 테스트"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content="test_2",
            img_key=None,
            original_img=None,
        )
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.content, "test_2")
        self.assertEqual(comment.img_key, None)
        self.assertEqual(comment.original_img, None)
        self.assertEqual(Comment.objects.count(), 3)

    def test_create_comment_image(self) -> None:
        """이미지 댓글 작성 테스트"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content=None,
            img_key="dev/comments/uuid_2.png",
            original_img="uuid_2.png",
        )
        self.assertEqual(comment.content, None)
        self.assertEqual(comment.img_key, "dev/comments/uuid_2.png")
        self.assertEqual(comment.original_img, "uuid_2.png")
        self.assertEqual(Comment.objects.count(), 3)

    def test_create_comment_like(self) -> None:
        """댓글 좋아요 생성 성공 테스트"""
        comment_like = CommentLike.objects.create(
            user=self.user,
            comment=self.comment_image,
        )
        self.assertEqual(comment_like.user, self.user)
        self.assertEqual(comment_like.comment, self.comment_image)
        self.assertEqual(CommentLike.objects.count(), 2)

    def test_fail_create_comment_like(self) -> None:
        """comment와 user unique_together 적용 테스트"""
        with self.assertRaises(Exception):
            CommentLike.objects.create(
                user=self.user,
                comment=self.comment_no_image,
            )
            self.comment_like.refresh_from_db()
            self.assertEqual(CommentLike.objects.count(), 1)

    def test_delete_comment_comment_like(self) -> None:
        """삭제된 comment에 대한 좋아요 CASCADE 적용 test"""
        self.comment_no_image.delete()
        self.assertEqual(CommentLike.objects.count(), 0)
