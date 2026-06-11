from django.db import transaction

from apps.comments.models import Comment
from apps.comments.services import delete_comment
from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from tests.test_comments.core import CommentBaseTest


class TestCommentDeleteService(CommentBaseTest):

    def test_delete_comment(self) -> None:
        """로그인한 유저의 본인이 작성한 댓글 삭제 service 성공 테스트"""
        delete_comment(self.comment_content.id, self.user_1)
        self.assertEqual(Comment.objects.count(), 1)

    def test_fail_other_user_comment(self) -> None:
        """로그인한 유저의 본인이 작성하지 않은 댓글 삭제 service 실패 테스트"""
        with self.assertRaises(ForbiddenException):
            with transaction.atomic():
                delete_comment(self.comment_content.id, self.user_2)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_none_comment_delete_comment(self) -> None:
        """로그인한 유저의 존재하지 않는 댓글 삭제 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            with transaction.atomic():
                delete_comment(self.none_comment_id, self.user_1)
        self.assertEqual(Comment.objects.count(), 2)
