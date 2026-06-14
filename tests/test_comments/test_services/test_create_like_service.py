from apps.comments.services.services import create_comment_like
from apps.core.exceptions.exception import ConflictException, NotFoundException
from tests.test_comments.core import CommentLikeBaseTest


class TestCommentLikeCreateService(CommentLikeBaseTest):

    def test_create_like_service(self):
        """댓글 좋아요 생성 service 성공 테스트 후 재시도시 실패 테스트"""
        result = create_comment_like(self.comment_content.id, self.user_2)
        self.assertEqual(result["is_liked"], True)
        self.assertEqual(result["like_count"], 1)
        with self.assertRaises(ConflictException):
            create_comment_like(self.comment_content.id, self.user_2)

    def test_no_comment_like_service(self):
        """없는 댓글에 대한 좋아요 생성 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            create_comment_like("없는아이디", self.user_2)
