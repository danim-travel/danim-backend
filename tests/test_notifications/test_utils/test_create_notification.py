from datetime import date

from django.core.cache import cache

from apps.comments.models import Comment
from apps.directmessages.models import Conversation
from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.posts.models import Post
from apps.users.models import LoginType, User
from tests.test_notifications.core.base import NotificationsBaseTest


class TestCreateNotification(NotificationsBaseTest):

    def setUp(self):
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
