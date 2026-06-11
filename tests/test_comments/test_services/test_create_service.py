from apps.comments.models import Comment
from apps.comments.services import create_comment
from apps.core.exceptions.exception import NotFoundException
from apps.core.storage.s3 import s3_svc
from tests.test_comments.core import CommentBaseTest


class TestCommentCreateService(CommentBaseTest):
    """create_comment 서비스 메서드 테스트"""

    def test_create_comment_content(self) -> None:
        """content만 있는 댓글 작성 서비스 메서드 성공 테스트"""
        new_comment = create_comment(self.data_for_content, self.user_1)
        self.assertEqual(Comment.objects.count(), 3)
        self.assertEqual(new_comment.content, self.data_for_content["content"])
        self.assertEqual(new_comment.img_key, None)
        self.assertEqual(new_comment.original_img, None)

    def test_create_comment_img(self) -> None:
        """img 댓글 작성 서비스 메서드 성공 테스트"""
        new_comment = create_comment(self.data_for_img, self.user_1)
        self.assertEqual(Comment.objects.count(), 3)
        self.assertEqual(new_comment.content, None)
        self.assertEqual(new_comment.img_key, self.data_for_img["comment_img"]["key"])
        self.assertEqual(new_comment.original_img, "dog.png")

    def test_fail_create_comment(self) -> None:
        """존재하지 않는 게시글에 댓글 작성 시도 실패 테스트"""
        with self.assertRaises(NotFoundException):
            create_comment(self.fail_data_for_none_post, self.user_1)
        self.assertEqual(Comment.objects.count(), 2)
