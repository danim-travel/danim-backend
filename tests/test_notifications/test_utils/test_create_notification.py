from datetime import date
from unittest.mock import patch

from django.core.cache import cache

from apps.comments.models import Comment
from apps.directmessages.models import Conversation
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.notifications.utils.create_notification import NOTI_DEDUP_TTL, create_noti
from apps.posts.models import Post
from apps.users.models import LoginType, User
from tests.test_notifications.core.base import NotificationsBaseTest


class TestCreateNotification(NotificationsBaseTest):

    def setUp(self):
        from django.db.models.signals import post_save

        from apps.comments.models import Comment as CommentModel
        from apps.notifications.signals.signal import on_created_comment

        post_save.disconnect(on_created_comment, sender=CommentModel)
        super().setUp()
        self.message_1 = (
            f"{self.user_1.nickname}님이 회원님의 게시글에 댓글을 작성했습니다."
        )
        self.message_2 = (
            f"{self.user_1.nickname}님이 회원님의 댓글에 좋아요를 눌렀습니다."
        )
        self.message_3 = (
            f"{self.user_1.nickname}님이 회원님의 게시글에 좋아요를 눌렀습니다."
        )
        self.message_4 = f"{self.user_1.nickname}님이 회원님을 팔로우 했습니다."
        self.message_5 = f"{self.user_1.nickname}님이 회원님께 메세지를 보냈습니다."
        self.post = Post.objects.create(title="test_title", user=self.user_2)
        self.comment = Comment.objects.create(
            post=self.post,
            content="test_content",
        )
        self.user_3 = User.objects.create_user(
            email="test_4@example.com",
            name="test_4",
            nickname="test_4nickname",
            password="Password_4@123",
            phone_number="01032345678",
            birth_day=date(1973, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.conversation = Conversation.objects.create(
            user1=self.user_1, user2=self.user_2
        )

    def tearDown(self):
        from django.db.models.signals import post_save

        from apps.comments.models import Comment as CommentModel
        from apps.notifications.signals.signal import on_created_comment

        post_save.connect(on_created_comment, sender=CommentModel)
        cache.delete(f"user_{self.user_2.id}_unread_count")
        super().tearDown()

    def test_comment_create_notification(self):
        """게시글에 댓글 생성시 알림 생성 및 redis 캐시 갱신 테스트"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="comment",
            target_id=self.post.id,
        )
        noti = Notification.objects.get(receiver=self.user_2)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(noti.sender, self.user_1)
        self.assertEqual(noti.target_id, self.post.id)
        self.assertEqual(noti.notification_type, "comment")
        self.assertEqual(noti.message, self.message_1)
        self.assertEqual(noti.is_read, False)

        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_3,
            noti_type="comment",
            target_id=self.post.id,
        )
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 2)

    def test_comment_like_create_notification(self):
        """댓글 좋아요 생성 시 알림 생성 및 redis 캐시 갱신 테스트"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="comment_like",
            target_id=self.comment.post.id,
        )
        noti = Notification.objects.get(receiver=self.user_2)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(noti.sender, self.user_1)
        self.assertEqual(noti.target_id, self.post.id)
        self.assertEqual(noti.notification_type, "comment_like")
        self.assertEqual(noti.message, self.message_2)
        self.assertEqual(noti.is_read, False)

        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_3,
            noti_type="comment_like",
            target_id=self.comment.post.id,
        )
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 2)

    def test_post_like_create_notification(self):
        """게시글 좋아요 생성 시 알림 생성 및 redis 캐시 갱신 테스트"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="post_like",
            target_id=self.post.id,
        )
        noti = Notification.objects.get(receiver=self.user_2)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(noti.sender, self.user_1)
        self.assertEqual(noti.target_id, self.post.id)
        self.assertEqual(noti.notification_type, "post_like")
        self.assertEqual(noti.message, self.message_3)
        self.assertEqual(noti.is_read, False)

        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_3,
            noti_type="post_like",
            target_id=self.post.id,
        )
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 2)

    def test_follow_create_notification(self):
        """팔로우 생성시 알림 생성 및 redis 캐시 갱신 테스트"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="follow",
            target_id=self.user_1.id,
        )
        noti = Notification.objects.get(receiver=self.user_2)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(noti.sender, self.user_1)
        self.assertEqual(noti.target_id, self.user_1.id)
        self.assertEqual(noti.notification_type, "follow")
        self.assertEqual(noti.message, self.message_4)
        self.assertEqual(noti.is_read, False)

        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_3,
            noti_type="follow",
            target_id=self.user_3.id,
        )
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 2)

    def test_dm_create_notification(self):
        """DM 발송시 알림 생성 및 redis 캐시 갱신 테스트"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="dm",
            target_id=self.conversation.id,
        )
        noti = Notification.objects.get(receiver=self.user_2)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(noti.sender, self.user_1)
        self.assertEqual(noti.target_id, self.conversation.id)
        self.assertEqual(noti.notification_type, "dm")
        self.assertEqual(noti.message, self.message_5)
        self.assertEqual(noti.is_read, False)

        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_3,
            noti_type="dm",
            target_id=self.conversation.id,
        )
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 2)

    def test_same_receiver_sender_create_notification(self):
        """발신자와 수신자가 같을때 알림 생성 취소 테스트"""
        create_notification(
            receiver_id=self.user_1.id,
            sender=self.user_1,
            noti_type="comment",
            target_id=self.post.id,
        )
        self.assertEqual(Notification.objects.count(), 0)


class TestCreateNotificationDedup(NotificationsBaseTest):
    """알림 중복 생성 방지(dedup) 테스트.

    좋아요/팔로우는 취소 후 재실행을 반복하면 post_save(created=True)가 매번 발화해
    알림이 무제한 생성된다. celery worker가 큐를 소비하기 시작하면 즉시 문제가 되므로
    TTL 안에서는 한 번만 생성되어야 한다.
    """

    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(title="test_title", user=self.user_2)
        self.other_post = Post.objects.create(title="other_title", user=self.user_2)
        self._dedup_keys: list[str] = []

    def tearDown(self):
        for key in self._dedup_keys:
            cache.delete(key)
        cache.delete(f"user_{self.user_2.id}_unread_count")
        super().tearDown()

    def _notify(self, noti_type, target_id, sender=None):
        sender = sender or self.user_1
        self._dedup_keys.append(
            f"noti:dedup:{self.user_2.id}:{sender.id}:{noti_type}:{target_id}"
        )
        create_notification(
            receiver_id=self.user_2.id,
            sender=sender,
            noti_type=noti_type,
            target_id=target_id,
        )

    def test_post_like_repeat_creates_single_notification(self):
        """같은 유저가 같은 게시글에 좋아요를 반복해도 알림은 1건만 생성된다"""
        for _ in range(5):
            self._notify("post_like", self.post.id)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(cache.get(f"user_{self.user_2.id}_unread_count"), 1)

    def test_post_like_different_target_not_deduped(self):
        """대상 게시글이 다르면 각각 알림이 생성된다"""
        self._notify("post_like", self.post.id)
        self._notify("post_like", self.other_post.id)

        self.assertEqual(Notification.objects.count(), 2)

    def test_post_like_different_sender_not_deduped(self):
        """발신자가 다르면 각각 알림이 생성된다"""
        self._notify("post_like", self.post.id, sender=self.user_1)
        self._notify("post_like", self.post.id, sender=self.user_3)

        self.assertEqual(Notification.objects.count(), 2)

    def test_follow_repeat_creates_single_notification(self):
        """같은 유저가 팔로우를 반복해도 알림은 1건만 생성된다"""
        for _ in range(3):
            self._notify("follow", self.user_1.id)

        self.assertEqual(Notification.objects.count(), 1)

    def test_comment_not_deduped(self):
        """댓글은 dedup 대상이 아니다.

        target_id가 게시글 ID라 같은 게시글의 서로 다른 댓글이 같은 키로 뭉개진다.
        정상 알림이 막히면 안 되므로 dedup을 적용하지 않는다.
        """
        self._notify("comment", self.post.id)
        self._notify("comment", self.post.id)

        self.assertEqual(Notification.objects.count(), 2)

    def test_comment_like_not_deduped(self):
        """댓글 좋아요도 같은 이유로 dedup 대상이 아니다"""
        self._notify("comment_like", self.post.id)
        self._notify("comment_like", self.post.id)

        self.assertEqual(Notification.objects.count(), 2)

    def test_dedup_key_released_after_expiry(self):
        """TTL이 만료되면 같은 알림이 다시 생성된다"""
        self._notify("post_like", self.post.id)
        self.assertEqual(Notification.objects.count(), 1)

        cache.delete(self._dedup_keys[0])  # TTL 만료를 대체
        self._notify("post_like", self.post.id)

        self.assertEqual(Notification.objects.count(), 2)

    def test_dedup_key_is_set_with_configured_ttl(self):
        """dedup 키가 NOTI_DEDUP_TTL 값으로 설정된다"""
        with patch(
            "apps.notifications.utils.create_notification.cache.add", return_value=True
        ) as mock_add:
            self._notify("post_like", self.post.id)

        _, kwargs = mock_add.call_args
        self.assertEqual(kwargs["timeout"], NOTI_DEDUP_TTL)

    def test_different_receiver_not_deduped(self):
        """수신자가 다르면 각각 알림이 생성된다"""
        create_notification(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="follow",
            target_id=self.user_1.id,
        )
        create_notification(
            receiver_id=self.user_3.id,
            sender=self.user_1,
            noti_type="follow",
            target_id=self.user_1.id,
        )
        self._dedup_keys.append(
            f"noti:dedup:{self.user_2.id}:{self.user_1.id}:follow:{self.user_1.id}"
        )
        self._dedup_keys.append(
            f"noti:dedup:{self.user_3.id}:{self.user_1.id}:follow:{self.user_1.id}"
        )

        self.assertEqual(Notification.objects.count(), 2)

    def test_redis_failure_passes_through(self):
        """Redis 장애로 cache.add가 None을 반환하면 알림을 통과시킨다(fail-open)"""
        with patch(
            "apps.notifications.utils.create_notification.cache.add", return_value=None
        ):
            self._notify("post_like", self.post.id)
            self._notify("post_like", self.post.id)

        self.assertEqual(Notification.objects.count(), 2)

    def test_dedup_key_released_when_creation_fails(self):
        """생성 실패 시 선점한 키를 해제해 재시도가 정상 진행된다.

        키를 해제하지 않으면 celery 재시도(countdown 1·2·4초)가 전부 TTL 30초 안에
        들어와 중복으로 오인되고, 예외 없이 return하므로 태스크가 성공으로 기록되어
        알림이 영구 유실된다.
        """
        with patch(
            "apps.notifications.utils.create_notification.create_noti",
            side_effect=RuntimeError("일시 DB 오류"),
        ):
            with self.assertRaises(RuntimeError):
                self._notify("post_like", self.post.id)

        self.assertIsNone(cache.get(self._dedup_keys[0]))

        self._notify("post_like", self.post.id)
        self.assertEqual(Notification.objects.count(), 1)

    def test_task_retry_creates_notification_after_transient_failure(self):
        """일시 장애로 재시도된 태스크가 결국 알림을 생성한다"""
        calls = {"count": 0}
        original = create_noti

        def fail_once(*args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise RuntimeError("일시 DB 오류")
            return original(*args, **kwargs)

        self._dedup_keys.append(
            f"noti:dedup:{self.user_2.id}:{self.user_1.id}:post_like:{self.post.id}"
        )
        with patch(
            "apps.notifications.utils.create_notification.create_noti",
            side_effect=fail_once,
        ):
            with self.assertRaises(RuntimeError):
                create_notification(
                    receiver_id=self.user_2.id,
                    sender=self.user_1,
                    noti_type="post_like",
                    target_id=self.post.id,
                )
            # celery 재시도에 해당 — 키가 해제돼 있어야 통과한다
            create_notification(
                receiver_id=self.user_2.id,
                sender=self.user_1,
                noti_type="post_like",
                target_id=self.post.id,
            )

        self.assertEqual(calls["count"], 2)
        self.assertEqual(Notification.objects.count(), 1)
