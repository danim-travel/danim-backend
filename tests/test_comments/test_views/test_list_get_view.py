from apps.comments.models import Comment
from tests.test_comments.core import CommentBaseTest


class TestListGetView(CommentBaseTest):
    query_params: dict
    string_page_params: dict

    def setUp(self):
        super().setUp()
        mock_data = []
        for n in range(50):
            mock_data.append(
                Comment(
                    post=self.post,
                    user=self.user_1,
                    content=f"test{n}",
                    img_key=None,
                    original_img=None,
                )
            )
        Comment.objects.bulk_create(mock_data)
        self.query_params_1 = {
            "page_size": 10,
            "post_id": self.post.id,
        }
        self.none_post_query_params = {
            "page_size": 10,
            "post_id": "없는 게시글",
        }
        self.string_page_params = {
            "page_size": "string",
            "post_id": self.post.id,
        }
        self.under_page_size_params = {
            "page_size": -10,
            "post_id": self.post.id,
        }
        self.over_page_size_params = {
            "page_size": 101,
            "post_id": self.post.id,
        }

    def test_authenticated_user_get_list_view(self) -> None:
        """로그인한 유저 댓글 목록조회 view 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url, self.query_params_1)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)
        second_response = self.client.get(response.data["next"])
        self.assertIn("results", second_response.data)
        self.assertEqual(len(second_response.data["results"]), 10)
        self.assertIn("next", second_response.data)
        self.assertIsNotNone(second_response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_nonauthenticated_user_get_list_view(self) -> None:
        """비로그인 유저 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, self.query_params_1)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_fail_none_post_list_view(self) -> None:
        """없는 게시글 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url, self.none_post_query_params)
        self.assertEqual(response.status_code, 404)

    def test_string_page_size_get_list_view(self) -> None:
        """page_size가 문자열일때 목록 조회 view 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url, self.string_page_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_under_page_size_get_list_view(self) -> None:
        """page_size가 음수 일떄 맷글 목록 조회 pagination 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url, self.under_page_size_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_over_page_size_get_list_view(self) -> None:
        """page_size가 max_page_size의 초과할때 로그인한 유저의 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url, self.over_page_size_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 52)
        self.assertIn("next", response.data)
        self.assertIsNone(response.data["next"])
        self.assertEqual(response.status_code, 200)
