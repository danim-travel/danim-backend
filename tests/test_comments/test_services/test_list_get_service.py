from django.contrib.auth.models import AnonymousUser

from apps.comments.models import Comment
from apps.comments.services import get_comment_list
from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post
from apps.users.models import User
from tests.test_comments.core import CommentBaseTest


class TestCommentListGetService(CommentBaseTest):

    def test_get_list_queryset(self) -> None:
        """게시글 댓글 목록조회 성공 테스트"""
        queryset = get_comment_list(self.post.id, self.user)
        self.assertEqual(queryset.count(), 2)
        for comment in queryset:
            self.assertIsInstance(comment, Comment)
            self.assertIsInstance(comment.post, Post)
            self.assertIsInstance(comment.user, User)
            self.assertEqual(comment.post, self.post)
            self.assertTrue(hasattr(comment, "is_liked"))
            self.assertTrue(hasattr(comment, "like_count"))
            if comment.id == self.comment_content.id:
                self.assertTrue(comment.is_liked)
            else:
                self.assertFalse(comment.is_liked)

    def test_fail_get_list_queryset(self) -> None:
        """없는 게시글에 대한 조회 404 실패 테스트"""
        with self.assertRaises(NotFoundException):
            get_comment_list(self.fail_data_for_none_post["post_id"], self.user)

    def test_nonauthenticated_get_list_queryset(self) -> None:
        """비로그인 유저의 목록 조회 테스트"""
        queryset = get_comment_list(self.post.id, AnonymousUser())
        self.assertEqual(queryset.count(), 2)
        for comment in queryset:
            self.assertIsInstance(comment, Comment)
            self.assertIsInstance(comment.post, Post)
            self.assertIsInstance(comment.user, User)
            self.assertEqual(comment.post, self.post)
            self.assertTrue(hasattr(comment, "is_liked"))
            self.assertFalse(comment.is_liked)
            self.assertTrue(hasattr(comment, "like_count"))
