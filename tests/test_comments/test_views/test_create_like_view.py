from tests.test_comments.core import CommentLikeBaseTest


class TestCommentLikeCreateView(CommentLikeBaseTest):

    def test_create_comment_like_view(self):
        """로그인한 유저의 댓글 좋아요 생성 view 성공 테스트 후 재시도 시 실패 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["is_liked"], True)
        self.assertEqual(response.data["like_count"], 1)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 409)

    def test_unauthorized_comment_like_view(self):
        """비로그인한 유저의 댓글 좋아요 생성 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)
