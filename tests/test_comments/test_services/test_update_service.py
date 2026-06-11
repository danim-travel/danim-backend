from django.db import transaction

from apps.comments.models import Comment
from apps.comments.services import update_comment
from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from tests.test_comments.core import CommentBaseTest


class TestCommentUpdateService(CommentBaseTest):

    def test_update_content_service(self) -> None:
        """이미지 없는 댓글 content 수정 서비스 로직 성공 테스트"""
        mod_comment = update_comment(
            self.data_for_update_content, self.user_1, self.comment_content.id
        )
        self.assertEqual(mod_comment.id, self.comment_content.id)
        self.assertEqual(mod_comment.content, self.data_for_update_content["content"])
        self.assertEqual(mod_comment.img_key, self.comment_content.img_key)
        self.assertEqual(mod_comment.original_img, self.comment_content.original_img)
        self.assertEqual(Comment.objects.count(), 2)

    def test_update_comment_img_service(self) -> None:
        """이미지 있는 댓글 img_key,original_img 수정 서비스 로직 성공 테스트"""
        mod_comment = update_comment(
            self.data_for_update_img, self.user_1, self.comment_image.id
        )
        self.assertEqual(mod_comment.id, self.comment_image.id)
        self.assertEqual(mod_comment.content, self.comment_image.content)
        self.assertEqual(
            mod_comment.img_key, self.data_for_update_img["comment_img"]["key"]
        )
        self.assertEqual(
            mod_comment.original_img,
            self.data_for_update_img["comment_img"]["original_img"],
        )
        self.assertEqual(Comment.objects.count(), 2)

    def test_update_img_add_to_comment_content_service(self) -> None:
        """이미지 없는 댓글에 이미지 추가 서비스 로직 성공 테스트"""
        mod_comment = update_comment(
            self.data_for_update_img, self.user_1, self.comment_content.id
        )
        self.assertEqual(mod_comment.id, self.comment_content.id)
        self.assertEqual(mod_comment.content, self.comment_content.content)
        self.assertEqual(
            mod_comment.img_key, self.data_for_update_img["comment_img"]["key"]
        )
        self.assertEqual(
            mod_comment.original_img,
            self.data_for_update_img["comment_img"]["original_img"],
        )
        self.assertEqual(Comment.objects.count(), 2)

    def test_update_content_add_to_comment_img_service(self) -> None:
        """내용이 없는 댓글에 내용 추가 서비스 로직 성공 테스트"""
        mod_comment = update_comment(
            self.data_for_update_content, self.user_1, self.comment_image.id
        )
        self.assertEqual(mod_comment.id, self.comment_image.id)
        self.assertEqual(mod_comment.content, self.data_for_update_content["content"])
        self.assertEqual(mod_comment.img_key, self.comment_image.img_key)
        self.assertEqual(mod_comment.original_img, self.comment_image.original_img)
        self.assertEqual(Comment.objects.count(), 2)

    def test_fail_update_non_comment_service(self) -> None:
        """없는 댓글 수정 시도 서비스 로직 실패 테스트"""
        with self.assertRaises(NotFoundException):
            with transaction.atomic():
                mod_comment = update_comment(
                    self.data_for_update_content, self.user_1, self.none_comment_id
                )

    def test_fail_update_other_user_service(self) -> None:
        """다른 유저가 작성한 댓글 수정 시도 서비스 실패 테스트"""
        with self.assertRaises(ForbiddenException):
            with transaction.atomic():
                mod_comment = update_comment(
                    self.data_for_update_img, self.user_2, self.comment_content.id
                )
