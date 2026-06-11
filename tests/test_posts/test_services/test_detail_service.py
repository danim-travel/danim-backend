from datetime import date

from django.test import TestCase

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post, PostLike
from apps.posts.models.bookmark_model import BookMark
from apps.posts.services.detail_service import PostDetailService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostDetailServiceTest(TestCase):

    service: PostDetailService
    user: User
    other_user: User
    post: Post

    def setUp(self) -> None:
        self.service = PostDetailService()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create(
            email="other@example.com",
            name="other",
            nickname="other_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )

    def test_get_post_detail(self) -> None:
        """게시글 상세 조회 성공 테스트"""
        post = self.service.get_post_detail(self.post.id, self.user)
        assert post is not None
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.like_count, 0)
        self.assertEqual(post.comment_count, 0)
        self.assertFalse(post.is_liked)
        self.assertFalse(post.is_bookmarked)
        self.assertTrue(post.is_owner)

    def test_get_post_detail_is_liked(self) -> None:
        """좋아요한 게시글의 is_liked가 True인 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        post = self.service.get_post_detail(self.post.id, self.user)
        assert post is not None
        self.assertTrue(post.is_liked)

    def test_get_post_detail_is_bookmarked(self) -> None:
        """북마크한 게시글의 is_bookmarked가 True인 테스트"""
        BookMark.objects.create(post=self.post, user=self.user)
        post = self.service.get_post_detail(self.post.id, self.user)
        assert post is not None
        self.assertTrue(post.is_bookmarked)

    def test_get_post_detail_is_not_owner(self) -> None:
        """게시글 작성자가 아닌 경우 is_owner가 False인 테스트"""
        post = self.service.get_post_detail(self.post.id, self.other_user)
        assert post is not None
        self.assertFalse(post.is_owner)

    def test_fail_get_post_detail_not_found(self) -> None:
        """존재하지 않는 게시글 조회 시 NotFoundException 테스트"""
        with self.assertRaises(NotFoundException):
            self.service.get_post_detail("nonexistent_id", self.user)
