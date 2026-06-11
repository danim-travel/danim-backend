from apps.comments.models import Comment
from tests.test_comments.core import CommentBaseTest


class TestCreateView(CommentBaseTest):
    """CommentCreateView 관련 테스트"""

    def test_comment_create_view(self) -> None:
        """로그인한 유저의 댓글 생성 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, self.data_for_content)
        self.assertEqual(Comment.objects.count(), 3)
        self.assertEqual(response.status_code, 201)

    def test_fail_create_view(self) -> None:
        """로그인 하지 않은 유저의 댓글 생성 실패 테스트"""
        response = self.client.post(self.url, self.data_for_content)
        self.assertEqual(Comment.objects.count(), 2)
        self.assertEqual(response.status_code, 401)
