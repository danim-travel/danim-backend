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
                    user=self.user,
                    content=f"test{n}",
                    img_key=None,
                    original_img=None,
                )
            )
        Comment.objects.bulk_create(mock_data)
        self.query_params = {"page": 1, "page_size": 10, "post_id": self.post.id}
        self.next_page_params = {"page": 2, "page_size": 10, "post_id": self.post.id}
        self.last_page_params = {"page": 6, "page_size": 10, "post_id": self.post.id}
        self.none_post_id_params = {
            "page": 1,
            "page_size": 10,
            "post_id": "없는 게시글 id",
        }
        self.string_page_params = {
            "page": "이상한 값",
            "page_size": 10,
            "post_id": self.post.id,
        }
        self.string_page_size_params = {
            "page": 1,
            "page_size": "이상한 값",
            "post_id": self.post.id,
        }
        self.under_page_params = {"page": -1, "page_size": 10, "post_id": self.post.id}
        self.under_page_size_params = {
            "page": 1,
            "page_size": -10,
            "post_id": self.post.id,
        }
        self.over_page_size_params = {
            "page": 1,
            "page_size": 10000000,
            "post_id": self.post.id,
        }

    def test_authenticated_user_get_list_view(self) -> None:
        """로그인한 유저 댓글 목록조회 view 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.query_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_next_page_get_list_view(self) -> None:
        """page가 2일때 로그인한 유저의 댓글 목록조회 view 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.next_page_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNotNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_last_page_get_list_view(self) -> None:
        """page가 마지막 페이지 일때 로그인한 유저의 목록조회 view 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.last_page_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertIn("previous", response.data)
        self.assertIsNotNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_nonauthenticated_user_get_list_view(self) -> None:
        """비로그인 유저 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, self.query_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_fail_none_post_list_view(self) -> None:
        """없는 게시글 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.none_post_id_params)
        self.assertEqual(response.status_code, 404)

    def test_string_page_get_list_view(self) -> None:
        """page가 문자열 일때 댓글 목록 조회 pagination 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.string_page_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_string_page_size_get_list_view(self) -> None:
        """page_size가 문자열 일떄 댓글 목록 조회 pagination 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.string_page_size_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_under_page_get_list_view(self) -> None:
        """page가 음수 일때 댓글 목록 조회 pagination 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.under_page_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_under_page_size_get_list_view(self) -> None:
        """page_size가 음수 일떄 맷글 목록 조회 pagination 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.under_page_size_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNotNone(response.data["next"])
        self.assertEqual(response.status_code, 200)

    def test_over_page_size_get_list_view(self) -> None:
        """page_size가 max_page_size의 초과할때 로그인한 유저의 댓글 목록 조회 view 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, self.over_page_size_params)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 52)
        self.assertIn("previous", response.data)
        self.assertIsNone(response.data["previous"])
        self.assertIn("next", response.data)
        self.assertIsNone(response.data["next"])
        self.assertEqual(response.status_code, 200)
