from tests.test_comments.core import CommentBaseTest


class TestCommentUpdateView(CommentBaseTest):

    def test_update_content_view(self) -> None:
        """이미지 없는 댓글 수정 시도 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch(
            self.detail_url_content, self.data_for_update_content, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_update_img_view(self) -> None:
        """이미지 있는 댓글 수정 시도 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch(
            self.detail_url_img, self.data_for_update_img, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_fail_other_use_update_comment_view(self) -> None:
        """다른 사람의 댓글을 수정 시도 view 실패 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.patch(
            self.detail_url_content, self.data_for_update_content, format="json"
        )
        self.assertEqual(response.status_code, 403)

    def test_fail_nonauthenticated_user_update_comment_view(self) -> None:
        """비로그인 유저의 댓글 수정 시도 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            self.detail_url_content, self.data_for_update_content, format="json"
        )
        self.assertEqual(response.status_code, 401)
