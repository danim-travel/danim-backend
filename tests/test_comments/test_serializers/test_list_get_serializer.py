from apps.comments.serializers import CommentListSerializer
from apps.core.storage.s3 import s3_svc
from tests.test_comments.core import CommentBaseTest


class TestListGetSerializer(CommentBaseTest):

    def setUp(self):
        super().setUp()
        self.comment_image.is_liked = False
        self.comment_content.is_liked = True
        self.comment_image.like_count = 1
        self.comment_content.like_count = 1

    def test_list_get_serializer_image(self) -> None:
        """이미지 댓글 serializer 응답 데이터 검증 테스트"""
        assert self.comment_image.user is not None
        serializer = CommentListSerializer(self.comment_image)
        self.assertEqual(serializer.data["user"]["id"], self.comment_image.user_id)
        self.assertEqual(
            serializer.data["user"]["nickname"], self.comment_image.user.nickname
        )
        self.assertEqual(
            serializer.data["user"]["profile_img"], self.comment_image.user.profile_img
        )
        self.assertEqual(serializer.data["user"]["is_deleted"], False)
        self.assertEqual(serializer.data["comment_id"], self.comment_image.id)
        self.assertEqual(serializer.data["content"], self.comment_image.content)
        assert self.comment_image.img_key is not None
        self.assertEqual(
            serializer.data["comment_img"]["img_url"],
            s3_svc.create_img_url(self.comment_image.img_key),
        )
        self.assertEqual(
            serializer.data["comment_img"]["key"], self.comment_image.img_key
        )
        self.assertEqual(
            serializer.data["comment_img"]["original_img"],
            self.comment_image.original_img,
        )
        self.assertEqual(serializer.data["is_liked"], self.comment_image.is_liked)  # type: ignore[attr-defined]
        self.assertEqual(serializer.data["like_count"], self.comment_image.like_count)  # type: ignore[attr-defined]

    def test_list_get_serializer_content(self) -> None:
        """이미지 없는 댓글 serializer 응답 데이터 검증 테스트"""
        assert self.comment_content.user is not None
        serializer = CommentListSerializer(self.comment_content)
        self.assertEqual(serializer.data["user"]["id"], self.comment_content.user_id)
        self.assertEqual(
            serializer.data["user"]["nickname"], self.comment_content.user.nickname
        )
        self.assertEqual(
            serializer.data["user"]["profile_img"], self.comment_content.user.profile_img
        )
        self.assertEqual(serializer.data["user"]["is_deleted"], False)
        self.assertEqual(serializer.data["comment_id"], self.comment_content.id)
        self.assertEqual(serializer.data["content"], self.comment_content.content)
        self.assertEqual(serializer.data["comment_img"]["img_url"], None)
        self.assertEqual(
            serializer.data["comment_img"]["key"], self.comment_content.img_key
        )
        self.assertEqual(
            serializer.data["comment_img"]["original_img"],
            self.comment_content.original_img,
        )
        self.assertEqual(serializer.data["is_liked"], self.comment_content.is_liked)  # type: ignore[attr-defined]
        self.assertEqual(serializer.data["like_count"], self.comment_content.like_count)  # type: ignore[attr-defined]
