from apps.comments.models import Comment
from tests.test_comments.core import CommentBaseTest


class TestCommentDeleteView(CommentBaseTest):

    def setUp(self):
        super().setUp()
        self.none_comment_url = f"/api/v1/comments/{self.none_comment_id}/"

    def test_delete_comment_view(self) -> None:
        """로그인 유저 본인이 작성한 댓글 삭제 view 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.count(), 1)

    def test_fail_unauthenticated_delete_comment_view(self) -> None:
        """비로그인 유저의 댓글 삭제 view 실패 테스트"""
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_other_user_delete_comment_view(self) -> None:
        """로그인 유저의 본인지 작성하지 않은 댓글 삭제 view 실패 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_none_comment_delete_view(self) -> None:
        """로그인한 유저의 없는 댓글 삭제 view 실패 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.none_comment_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 2)
