from apps.comments.models import Comment
from tests.test_comments.core import CommentBaseTest


class TestCommentDeleteView(CommentBaseTest):

    def setUp(self):
        super().setUp()
        self.none_comment_url = f"/api/v1/comments/{self.none_comment_id}/"

    def test_delete_comment_view(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Comment.objects.count(), 1)

    def test_fail_unauthenticated_delete_comment_view(self) -> None:
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_otther_user_delete_comment_view(self) -> None:
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.detail_url_content)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_none_comment_delete_view(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(self.none_comment_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Comment.objects.count(), 2)
