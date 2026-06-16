from apps.comments.models import CommentLike
from apps.comments.services import delete_comment_like
from apps.core.exceptions.exception import NotFoundException
from tests.test_comments.core import CommentLikeBaseTest


class TestCommentLikeDeleteService(CommentLikeBaseTest):

    def setUp(self):
        super().setUp()
        self.comment_like = CommentLike.objects.create(
            comment=self.comment_content,
            user=self.user_1,
        )
        self.comment_like_2 = CommentLike.objects.create(
            comment=self.comment_content,
            user=self.user_2,
        )

    def test_delete_like(self):
        """댓글 좋아요 취소 service 성공 테스트"""
        result = delete_comment_like(self.comment_content.id, self.user_1)
        self.assertEqual(CommentLike.objects.count(), 1)
        self.assertEqual(result["is_liked"], False)
        self.assertEqual(result["like_count"], 1)

    def test_none_comment_id_delete_like(self):
        """없는 댓글 아이디로 댓글 좋아요 취소 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            delete_comment_like("없는아이디", self.user_1)
