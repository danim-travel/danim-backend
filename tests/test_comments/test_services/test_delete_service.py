from django.db import transaction

from apps.comments.models import Comment
from apps.comments.services import delete_comment
from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from tests.test_comments.core import CommentBaseTest


class TestCommentDeleteService(CommentBaseTest):

    def test_delete_comment(self) -> None:
        """로그인한 유저의 본인이 작성한 댓글 삭제 service 성공 테스트"""
        delete_comment(self.comment_content.id, self.user)
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
                delete_comment(self.none_comment_id, self.user)
        self.assertEqual(Comment.objects.count(), 2)

    def test_delete_comment_decrements_persisted_count_once(self) -> None:
        """삭제 1회 = comment_count 감소 1회. 같은 댓글 재삭제는 404 + 카운터 유지.

        무조건 -1 회귀가 생기면 카운터가 실제 댓글 수보다 작아지고
        0 도달 시 PositiveIntegerField CHECK 위반으로 남은 댓글 삭제가 500이 된다.
        """
        delete_comment(self.comment_content.id, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)  # 2 → 1 (DB 영속값)

        with self.assertRaises(NotFoundException):
            with transaction.atomic():
                delete_comment(self.comment_content.id, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)  # 중복 감소 없음
