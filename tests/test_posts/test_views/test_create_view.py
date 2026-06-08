from rest_framework import status

from tests.test_posts.core import PostBaseTest


class TestPostCreateView(PostBaseTest):

    def test_create_view(self) -> None:
        """post create view 성공 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.create_url, self.data_for_create_view, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_fail_nonauthenticated_request(self) -> None:
        """비로그인 유저의 게시글 생성 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.create_url, self.data_for_create_view)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
