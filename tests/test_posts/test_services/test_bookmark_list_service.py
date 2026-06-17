from datetime import date

from django.test import TestCase

from apps.posts.models import Post, PostLike
from apps.posts.models.bookmark_model import BookMark
from apps.posts.services.bookmark_list_service import BookmarkListService
from apps.users.models import User
from apps.users.models.models import LoginType


class BookmarkListServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = BookmarkListService()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.other_user = User.objects.create(
            email="other@example.com",
            name="other",
            nickname="other_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post1 = Post.objects.create(
            user=self.user, title="t1", description="d1", thumbnail="prod/p/1.jpg"
        )
        self.post2 = Post.objects.create(
            user=self.user, title="t2", description="d2", thumbnail="prod/p/2.jpg"
        )
        # user가 post1 → post2 순서로 북마크 (post2가 최근)
        self.bm1 = BookMark.objects.create(user=self.user, post=self.post1)
        self.bm2 = BookMark.objects.create(user=self.user, post=self.post2)
        # other_user는 post1만 북마크
        BookMark.objects.create(user=self.other_user, post=self.post1)

    def test_returns_only_my_bookmarks(self) -> None:
        """내 북마크만 반환한다"""
        result = self.service.get_bookmark_list(self.user)
        self.assertEqual(result.count(), 2)
        self.assertTrue(all(bm.user_id == self.user.id for bm in result))

    def test_ordered_by_recent_bookmark(self) -> None:
        """최근 북마크순(-id) 정렬"""
        result = list(self.service.get_bookmark_list(self.user))
        self.assertEqual(result[0].id, self.bm2.id)  # post2 (최근)
        self.assertEqual(result[1].id, self.bm1.id)

    def test_is_liked_annotation(self) -> None:
        """is_liked가 요청 유저 기준으로 annotate된다"""
        PostLike.objects.create(user=self.user, post=self.post2)
        liked_map = {bm.post_id: bm.is_liked for bm in self.service.get_bookmark_list(self.user)}
        self.assertTrue(liked_map[self.post2.id])
        self.assertFalse(liked_map[self.post1.id])

    def test_does_not_return_others_bookmarks(self) -> None:
        """다른 유저 북마크는 안 섞인다 (other_user는 자기 1개만)"""
        result = self.service.get_bookmark_list(self.other_user)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().post_id, self.post1.id)

    def test_empty_when_no_bookmark(self) -> None:
        """북마크 없는 유저는 빈 결과"""
        empty_user = User.objects.create(
            email="empty@example.com",
            name="empty",
            nickname="empty_nick",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.assertEqual(self.service.get_bookmark_list(empty_user).count(), 0)
