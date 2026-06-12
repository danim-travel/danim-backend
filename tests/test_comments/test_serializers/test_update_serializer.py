from apps.comments.serializers import (
    CommentUpdateResponseSerializer,
    CommentUpdateSerializer,
)
from tests.test_comments.core import CommentBaseTest


class TestCommentUpdateSerializer(CommentBaseTest):

    def test_update_serializer_request_content(self) -> None:
        """이미지 없는 댓글 수정 입력 데이터 검증 serializer 성공 테스트"""
        serializer = CommentUpdateSerializer(data=self.data_for_content)
        self.assertTrue(serializer.is_valid())

    def test_update_serializer_request_img(self) -> None:
        """이미지 있는 댓글 수정 입력 데이터 검증 serializer 성공 테스트"""
        serializer = CommentUpdateSerializer(data=self.data_for_img)
        self.assertTrue(serializer.is_valid())

    def test_fail_update_serializer_request_content(self) -> None:
        """이미지 없는 댓글 수정 입력 데이터 검증 serializer 글자수 초과 실패 테스트"""
        serializer = CommentUpdateSerializer(data=self.fail_data_for_content)
        self.assertFalse(serializer.is_valid())

    def test_fail_update_serializer_request_img(self) -> None:
        """이미지 있는 댓글 수정 입력 데이터 검증 serializer 파일명 글자수 초과 및 key 글자수 초과 실패 테스트"""
        serializer = CommentUpdateSerializer(data=self.fail_data_for_img)
        self.assertFalse(serializer.is_valid())

    def test_update_serializer_response_content(self) -> None:
        """수정된 이미지 없는 댓글 데이터 직렬화 serializer 성공 테스트"""
        serializer = CommentUpdateResponseSerializer(self.comment_content)
        self.assertEqual(serializer.data["content"], self.comment_content.content)
        self.assertEqual(
            serializer.data["comment_img"]["key"], self.comment_content.img_key
        )
        self.assertEqual(
            serializer.data["comment_img"]["original_img"],
            self.comment_content.original_img,
        )
        self.assertEqual(serializer.data["comment_img"]["img_url"], None)
        self.assertEqual(serializer.data["post_id"], self.comment_content.post_id)
        self.assertEqual(serializer.data["user_id"], self.comment_content.user_id)

    def test_update_serializer_response_img(self) -> None:
        """수정된 이미지 있는 댓글 데이터 직렬화 serializer 성공 테스트"""
        serializer = CommentUpdateResponseSerializer(self.comment_image)
        self.assertEqual(serializer.data["content"], self.comment_image.content)
        self.assertEqual(
            serializer.data["comment_img"]["key"], self.comment_image.img_key
        )
        self.assertEqual(
            serializer.data["comment_img"]["original_img"],
            self.comment_image.original_img,
        )
        assert self.comment_image.img_key is not None
        img_url = serializer.data["comment_img"]["img_url"]
        self.assertIn(self.comment_image.img_key, img_url)
        self.assertIn("X-Amz-Signature", img_url)
        self.assertEqual(serializer.data["post_id"], self.comment_image.post_id)
        self.assertEqual(serializer.data["user_id"], self.comment_image.user_id)
