from unittest.mock import patch

from apps.comments.models import Comment, CommentLike
from apps.directmessages.models import Conversation, Message
from apps.follows.models import Follows
from apps.posts.models import Post, PostLike
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationSignal(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.post = Post.objects.create(title="tt-tt", user=self.user_2)
        self.comment = Comment.objects.create(
            post=self.post,
            user=self.user_2,
            content="tt-tt-comment",
        )

    @patch("apps.notifications.signals.signal.create_notification")
    def test_comment_signal(self, mock_noti):
        comment = Comment.objects.create(
            post=self.post, user=self.user_1, content="user_1"
        )
        mock_noti.assert_called_once_with(
            receiver_id=comment.post.user_id,
            sender=comment.user,
            noti_type="comment",
            target_id=comment.post_id,
        )

    @patch("apps.notifications.signals.signal.create_notification")
    def test_comment_like_signal(self, mock_noti):
        comment_like = CommentLike.objects.create(comment=self.comment, user=self.user_1)
        mock_noti.assert_called_once_with(
            receiver_id=comment_like.comment.user_id,
            sender=comment_like.user,
            noti_type="comment_like",
            target_id=comment_like.comment.post_id,
        )

    @patch("apps.notifications.signals.signal.create_notification")
    def test_post_like_signal(self, mock_noti):
        post_like = PostLike.objects.create(post=self.post, user=self.user_1)
        mock_noti.assert_called_once_with(
            receiver_id=post_like.post.user_id,
            sender=post_like.user,
            noti_type="post_like",
            target_id=post_like.post_id,
        )

    @patch("apps.notifications.signals.signal.create_notification")
    def test_follow_signal(self, mock_noti):
        follow = Follows.objects.create(following=self.user_2, follower=self.user_1)
        mock_noti.assert_called_once_with(
            receiver_id=follow.following_id,
            sender=follow.follower,
            noti_type="follow",
            target_id=follow.follower_id,
        )

    @patch("apps.notifications.signals.signal.create_notification")
    def test_message_signal(self, mock_noti):
        conversation = Conversation.objects.create(user1=self.user_1, user2=self.user_2)
        Message.objects.create(
            conversation=conversation, sender=self.user_1, content="test"
        )
        mock_noti.assert_called_once_with(
            receiver_id=self.user_2.id,
            sender=self.user_1,
            noti_type="dm",
            target_id=conversation.id,
        )
