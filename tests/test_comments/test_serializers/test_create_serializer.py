from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
)
from apps.core.storage.s3 import s3_svc
from tests.test_comments.core import CommentBaseTest


class TestCommentCreateSerializer(CommentBaseTest):
    """Comment 생성 관련 serializer 검증 테스트"""

    def test_create_serializer_content(self) -> None:
        """content만 있는 댓글 생성 요청 데이터 serializer 검증 성공 테스트"""
        serializer = CommentCreateSerializer(data=self.data_for_content)
        self.assertTrue(serializer.is_valid())

    def test_create_serializer_img(self) -> None:
        """img 댓글 생성 요청 데이터 serializer 검증 성공 테스트"""
        serializer = CommentCreateSerializer(data=self.data_for_img)
        self.assertTrue(serializer.is_valid())

    def test_fail_create_serializer(self) -> None:
        """둘다 입력 안한 댓글 생성 요청 데이터 serializer 검증 실패 테스트"""
        serializer = CommentCreateSerializer(data=self.fail_data_for_only_post)
        self.assertFalse(serializer.is_valid())

    def test_fail_create_serializer_content(self) -> None:
        """content 100자 이상 댓글 생성 요청 데이터 serializer 검증 실패 테스트"""
        serializer = CommentCreateSerializer(data=self.fail_data_for_content)
        self.assertFalse(serializer.is_valid())

    def test_fail_create_serializer_img(self) -> None:
        """img의 key 255자 및 original_img 100자 이상 댓글 이미지 생성 요청 데이터 serializer 검증 실패 테스트"""
        serializer = CommentCreateSerializer(data=self.fail_data_for_img)
        self.assertFalse(serializer.is_valid())

    def test_response_serializer_content(self) -> None:
        """content comment 객체 응답 serializer 검증 성공 테스트"""
        serializer = CommentCreateResponseSerializer(self.comment_content)
        self.assertEqual(serializer.data["content"], self.comment_content.content)
        self.assertIsNone(serializer.data["comment_img"]["key"])
        self.assertIsNone(serializer.data["comment_img"]["original_img"])

    def test_response_serializer_img(self) -> None:
        """image comment 객체 응답 serializer 검증 성공 테스트"""
        serializer = CommentCreateResponseSerializer(self.comment_image)
        self.assertEqual(
            serializer.data["comment_img"]["key"], self.comment_image.img_key
        )
        self.assertEqual(
            serializer.data["comment_img"]["original_img"],
            self.comment_image.original_img,
        )
        assert self.comment_image.img_key is not None
        self.assertEqual(
            serializer.data["comment_img"]["img_url"],
            s3_svc.create_img_url(self.comment_image.img_key),
        )
        self.assertIsNone(serializer.data["content"])
