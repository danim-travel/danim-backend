from datetime import date

from django.test import TestCase

from apps.follows.models.models import Follows
from apps.posts.models import Post, PostLike
from apps.posts.models.bookmark_model import BookMark
from apps.posts.services.main_list_service import PostMainListService
from apps.users.models import User
from apps.users.models.models import LoginType


class PostMainListServiceTest(TestCase):

    service: PostMainListService
    user: User
    author: User
    other_user: User
    post: Post
    other_post: Post

    def setUp(self) -> None:
        self.service = PostMainListService()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.author = User.objects.create(
            email="author@example.com",
            name="author",
            nickname="author_nickname",
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
        Follows.objects.create(follower=self.user, following=self.author)
        self.post = Post.objects.create(
            user=self.author,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.other_post = Post.objects.create(
            user=self.other_user,
            title="other_title",
            description="other_description",
            thumbnail="prod/posts/thumbnail/other_uuid.jpg",
        )

    def test_get_main_list(self) -> None:
        """팔로잉 피드 게시글 목록 조회 성공 테스트"""
        queryset = self.service.get_main_list(self.user)
        self.assertEqual(queryset.count(), 1)
        post = queryset.first()
        assert post is not None
        self.assertEqual(post.id, self.post.id)

    def test_get_main_list_excludes_non_following(self) -> None:
        """팔로우하지 않은 유저의 게시글은 조회되지 않는 테스트"""
        queryset = self.service.get_main_list(self.user)
        post_ids = list(queryset.values_list("id", flat=True))
        self.assertNotIn(self.other_post.id, post_ids)

    def test_get_main_list_is_liked(self) -> None:
        """좋아요한 게시글의 is_liked가 True인 테스트"""
        PostLike.objects.create(post=self.post, user=self.user)
        queryset = self.service.get_main_list(self.user)
        post = queryset.first()
        assert post is not None
        self.assertTrue(post.is_liked)

    def test_get_main_list_is_bookmarked(self) -> None:
        """북마크한 게시글의 is_bookmarked가 True인 테스트"""
        BookMark.objects.create(post=self.post, user=self.user)
        queryset = self.service.get_main_list(self.user)
        post = queryset.first()
        assert post is not None
        self.assertTrue(post.is_bookmarked)

    def test_get_main_list_empty(self) -> None:
        """팔로우한 유저가 없을 때 빈 목록 반환 테스트"""
        queryset = self.service.get_main_list(self.other_user)
        self.assertEqual(queryset.count(), 0)
