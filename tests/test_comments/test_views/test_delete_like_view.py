from apps.comments.models import CommentLike
from tests.test_comments.core import CommentLikeBaseTest


class TestCommentLikeDeleteView(CommentLikeBaseTest):

    def setUp(self):
        super().setUp()
        self.comment_like = CommentLike.objects.create(
            comment=self.comment_content,
            user=self.user_1,
        )
        self.comment_content.like_count = 1
        self.comment_content.save()
        self.none_comment_url = f"/api/v1/comments/없는아이디/like"

    def test_delete_like(self):
        """로그인한 유저의 댓글 좋아요 취소 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_liked"], False)
        self.assertEqual(response.data["like_count"], 0)

    def test_unauthenticated_user_like(self):
        """비로그인한 유저의 댓글 좋아요 취소 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_none_comment_id_delete_like(self):
        """없는 댓글 아이디에 해당 댓글 좋아요 취소 view 실패 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.none_comment_url)
        self.assertEqual(response.status_code, 404)
