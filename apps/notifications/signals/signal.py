from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.comments.models import Comment, CommentLike
from apps.directmessages.models import Message
from apps.follows.models import Follows
from apps.notifications.utils import create_notification
from apps.posts.models import PostLike


@receiver(post_save, sender=Comment)
def on_created_comment(sender, instance, created, **kwargs):
    if created:
        create_notification(
            receiver_id=instance.post.user_id,
            sender=instance.user,
            noti_type="comment",
            target_id=instance.post_id,
        )


@receiver(post_save, sender=CommentLike)
def on_created_comment_like(sender, instance, created, **kwargs):
    if created:
        create_notification(
            receiver_id=instance.comment.user_id,
            sender=instance.user,
            noti_type="comment_like",
            target_id=instance.comment.post_id,
        )


@receiver(post_save, sender=PostLike)
def on_created_post_like(sender, instance, created, **kwargs):
    if created:
        create_notification(
            receiver_id=instance.post.user_id,
            sender=instance.user,
            noti_type="post_like",
            target_id=instance.post_id,
        )


@receiver(post_save, sender=Follows)
def on_created_follow(sender, instance, created, **kwargs):
    if created:
        create_notification(
            receiver_id=instance.following_id,
            sender=instance.follower,
            noti_type="follow",
            target_id=instance.following_id,
        )


@receiver(post_save, sender=Message)
def on_created_message(sender, instance, created, **kwargs):
    if created:
        receiver_id = (
            instance.conversation.user1_id
            if instance.sender_id == instance.conversavtion.user2_id
            else instance.conversation.user2_id
        )
        create_notification(
            receiver_id=receiver_id,
            sender=instance.sender,
            noti_type="dm",
            target_id=instance.conversation_id,
        )
