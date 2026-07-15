from datetime import date

from django.test import TestCase

from apps.blocks.models import Block
from apps.blocks.services import (
    block_user,
    get_block_list,
    is_blocked_between,
    unblock_user,
)
from apps.core.exceptions.exception import (
    ConflictException,
    NotFoundException,
    ValidationException,
)
from apps.follows.models.models import Follows
from apps.users.models import User


def _make_user(tag: str) -> User:
    return User.objects.create_user(
        email=f"{tag}@example.com",
        password="Password@1",
        nickname=f"{tag}_nick",
        name=tag,
        birth_day=date(1995, 1, 1),
        is_active=True,  # create_user 기본값은 비활성 — 대화 생성의 is_active 필터 통과용
    )


class BlockServiceTest(TestCase):
    user_a: User
    user_b: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user_a = _make_user("usera")
        cls.user_b = _make_user("userb")

    def test_block_creates_relation(self) -> None:
        block_user(self.user_a, self.user_b.id)
        self.assertTrue(
            Block.objects.filter(blocker=self.user_a, blocked=self.user_b).exists()
        )
        self.assertTrue(is_blocked_between(self.user_a.id, self.user_b.id))
        # 방향 무관 — 반대 방향으로 조회해도 차단 관계
        self.assertTrue(is_blocked_between(self.user_b.id, self.user_a.id))

    def test_block_severs_follows_both_ways(self) -> None:
        """차단 시 기존 팔로우가 양방향 모두 끊긴다"""
        Follows.objects.create(follower=self.user_a, following=self.user_b)
        Follows.objects.create(follower=self.user_b, following=self.user_a)

        block_user(self.user_a, self.user_b.id)

        self.assertEqual(Follows.objects.count(), 0)

    def test_block_self_rejected(self) -> None:
        with self.assertRaises(ValidationException):
            block_user(self.user_a, self.user_a.id)

    def test_block_duplicate_conflict(self) -> None:
        block_user(self.user_a, self.user_b.id)
        with self.assertRaises(ConflictException):
            block_user(self.user_a, self.user_b.id)

    def test_block_unknown_user_not_found(self) -> None:
        with self.assertRaises(NotFoundException):
            block_user(self.user_a, "01ZZZZZZZZZZZZZZZZZZZZZZZZ")

    def test_unblock(self) -> None:
        block_user(self.user_a, self.user_b.id)
        unblock_user(self.user_a, self.user_b.id)
        self.assertFalse(is_blocked_between(self.user_a.id, self.user_b.id))

    def test_unblock_without_block_not_found(self) -> None:
        with self.assertRaises(NotFoundException):
            unblock_user(self.user_a, self.user_b.id)

    def test_unblock_only_releases_own_direction(self) -> None:
        """상대가 나를 차단한 상태에서 내 unblock은 불가(내 차단이 없으므로 404),
        상대의 차단은 그대로 유효하다"""
        block_user(self.user_b, self.user_a.id)
        with self.assertRaises(NotFoundException):
            unblock_user(self.user_a, self.user_b.id)
        self.assertTrue(is_blocked_between(self.user_a.id, self.user_b.id))

    def test_block_list(self) -> None:
        block_user(self.user_a, self.user_b.id)
        result = get_block_list(self.user_a)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().blocked_id, self.user_b.id)
        # 나를 차단한 목록이 아니라 내가 차단한 목록
        self.assertEqual(get_block_list(self.user_b).count(), 0)
