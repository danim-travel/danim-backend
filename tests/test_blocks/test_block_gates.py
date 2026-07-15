"""차단이 각 상호작용 게이트에서 실제로 막히는지 검증.

차단 기능의 가치는 모델이 아니라 게이트에 있다 — 팔로우·대화 생성·댓글·알림
네 경로가 전부 막혀야 '차단'이다 (DM 소켓 게이트는 consumer 통합테스트 범위).
"""

from datetime import date

from django.test import TestCase

from apps.blocks.services import block_user
from apps.core.exceptions.exception import ForbiddenException
from apps.follows.services.services import create_follow
from apps.notifications.models.model import Notification
from apps.posts.models import Post
from apps.users.models import User


def _make_user(tag: str) -> User:
    return User.objects.create_user(
        email=f"{tag}@example.com",
        password="Password@1",
        nickname=f"{tag}_nick",
        name=tag,
        birth_day=date(1995, 1, 1),
    )


class BlockGatesTest(TestCase):

    def setUp(self) -> None:
        self.blocker = _make_user("blocker")
        self.blocked = _make_user("blocked")
        block_user(self.blocker, self.blocked.id)

    def test_follow_gate_both_directions(self) -> None:
        """차단 관계에서는 어느 방향으로도 팔로우 불가"""
        with self.assertRaises(ForbiddenException):
            create_follow(self.blocked.id, self.blocker)
        with self.assertRaises(ForbiddenException):
            create_follow(self.blocker.id, self.blocked)

    def test_conversation_gate_both_directions(self) -> None:
        """차단 관계에서는 어느 방향으로도 대화 생성 불가"""
        from apps.directmessages.services.conversation_create_service import (
            get_or_create_conversation,
        )

        with self.assertRaises(ForbiddenException):
            get_or_create_conversation(self.blocked.id, self.blocker)
        with self.assertRaises(ForbiddenException):
            get_or_create_conversation(self.blocker.id, self.blocked)

    def test_comment_gate(self) -> None:
        """차단 관계의 게시글에는 댓글 작성 불가 (양방향)"""
        from apps.comments.services import create_comment

        post_by_blocker = Post.objects.create(user=self.blocker, title="t")
        with self.assertRaises(ForbiddenException):
            create_comment({"post_id": post_by_blocker.id, "content": "c"}, self.blocked)

        post_by_blocked = Post.objects.create(user=self.blocked, title="t2")
        with self.assertRaises(ForbiddenException):
            create_comment({"post_id": post_by_blocked.id, "content": "c"}, self.blocker)

    def test_notification_gate(self) -> None:
        """차단 관계면 알림이 생성되지 않는다 (중앙 게이트)"""
        from apps.notifications.utils import create_notification

        create_notification(
            receiver_id=self.blocked.id,
            sender=self.blocker,
            noti_type="follow",
            target_id=self.blocker.id,
        )
        create_notification(
            receiver_id=self.blocker.id,
            sender=self.blocked,
            noti_type="follow",
            target_id=self.blocked.id,
        )
        self.assertEqual(Notification.objects.count(), 0)

    def test_notification_passes_without_block(self) -> None:
        """차단이 없으면 알림은 정상 생성 — 게이트 과차단 회귀 방지"""
        from apps.notifications.utils import create_notification

        stranger = _make_user("stranger")
        create_notification(
            receiver_id=stranger.id,
            sender=self.blocker,
            noti_type="follow",
            target_id=self.blocker.id,
        )
        self.assertEqual(Notification.objects.filter(receiver_id=stranger.id).count(), 1)
