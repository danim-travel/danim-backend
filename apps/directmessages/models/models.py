from django.db import models

from apps.core.models import BaseModel
from apps.users.models import User


class Conversation(BaseModel):
    user1 = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="conversations_as_user1"
    )
    user2 = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="conversations_as_user2"
    )
    user1_left_at = models.DateTimeField(null=True, blank=True)
    user2_left_at = models.DateTimeField(null=True, blank=True)
    user1_last_read_at = models.DateTimeField(null=True, blank=True)
    user2_last_read_at = models.DateTimeField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversations"
        constraints = [
            models.UniqueConstraint(fields=["user1", "user2"], name="unique_conversation")
        ]
        indexes = [models.Index(fields=["-last_message_at"])]


class Message(BaseModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="sent_messages"
    )
    content = models.TextField(null=True, blank=True)
    img_url = models.CharField(max_length=500, null=True, blank=True)
    img_key = models.CharField(max_length=500, null=True, blank=True)
    original_img = models.CharField(max_length=255, null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = "messages"
        indexes = [models.Index(fields=["conversation", "id"])]
