from django.test import TestCase

from apps.comments.serializers.presigned_serializer import CommentPresignedSerializer
from apps.comments.views.views import CommentPresignedURLView
from apps.core.exceptions.exception import ValidationException


class TestCommentPresignedSerializer(TestCase):
    """CommentPresignedSerializer 검증 테스트"""

    def test_gif_allowed(self) -> None:
        """댓글 presigned serializer gif 허용 테스트"""
        serializer = CommentPresignedSerializer(data={"original_img": "test.gif"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["extension"], ".gif")
        self.assertEqual(serializer.validated_data["content_type"], "image/gif")

    def test_jpg_allowed(self) -> None:
        """댓글 presigned serializer jpg 허용 테스트"""
        serializer = CommentPresignedSerializer(data={"original_img": "test.jpg"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["extension"], ".jpg")
        self.assertEqual(serializer.validated_data["content_type"], "image/jpeg")

    def test_png_allowed(self) -> None:
        """댓글 presigned serializer png 허용 테스트"""
        serializer = CommentPresignedSerializer(data={"original_img": "test.png"})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data["extension"], ".png")
        self.assertEqual(serializer.validated_data["content_type"], "image/png")

    def test_invalid_extension(self) -> None:
        """댓글 presigned serializer 허용되지 않는 확장자 테스트"""
        serializer = CommentPresignedSerializer(data={"original_img": "test.pdf"})
        with self.assertRaises(ValidationException):
            serializer.is_valid(raise_exception=True)

    def test_view_uses_comment_serializer(self) -> None:
        """CommentPresignedURLView는 반드시 CommentPresignedSerializer를 사용해야 한다."""
        self.assertIs(
            CommentPresignedURLView.request_serializer_class,
            CommentPresignedSerializer,
        )
