from django.db import transaction

from apps.comments.models import Comment, CommentLike
from tests.test_comments.core import CommentBaseTest


class CommentTest(CommentBaseTest):
    """comment와 comment_like 모델 테스트"""

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
            with transaction.atomic():
                CommentLike.objects.create(
                    user=self.user,
                    comment=self.comment_content,
                )
        self.comment_like.refresh_from_db()
        self.assertEqual(CommentLike.objects.count(), 1)

    def test_delete_comment_comment_like(self) -> None:
        """삭제된 comment에 대한 좋아요 CASCADE 적용 test"""
        self.comment_content.delete()
        self.assertEqual(CommentLike.objects.count(), 0)
