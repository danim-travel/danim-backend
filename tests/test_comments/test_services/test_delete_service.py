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
        """삭제 1회 = comment_count 감소 1회(DB 영속값) + 재삭제는 404·카운터 유지.

        주의: 서비스가 방어하는 실제 결함(소유권 조회~삭제 사이 TOCTOU 경합의
        무조건 -1)은 단일 스레드 유닛테스트로 재현할 수 없다 — 순차 재삭제는
        최상단 조회 가드에서 이미 404가 난다. 이 테스트는 "1회 삭제 = 1회 감소"의
        영속 계약을 고정하는 가드이며, 경합 경로 자체는 코드의
        `if not deleted:` 분기(services.py delete_comment)가 담당한다.
        """
        delete_comment(self.comment_content.id, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)  # 2 → 1 (DB 영속값)

        with self.assertRaises(NotFoundException):
            with transaction.atomic():
                delete_comment(self.comment_content.id, self.user)
        self.post.refresh_from_db()
        self.assertEqual(self.post.comment_count, 1)  # 중복 감소 없음
