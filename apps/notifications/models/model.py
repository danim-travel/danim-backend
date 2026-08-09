from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class TargetChoices(models.TextChoices):
    """알림에 대한 정보를 확인 할 수 있는 위치"""

    USER = "user"
    POST = "post"
    DM = "dm"
    INQUIRY = "inquiry"


class NotificationType(models.TextChoices):
    """알림 발생 원인"""

    FOLLOW = "follow"
    COMMENT = "comment"
    COMMENT_LIKE = "comment_like"
    POST_LIKE = "post_like"
    DM = "dm"
    # 운영진 답변 알림. 다른 종류와 달리 sender가 없다(시스템 발신) — 자세한 이유는
    # apps/supports/tasks.py 참고.
    INQUIRY_ANSWERED = "inquiry_answered"


class Notification(BaseModel):

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="sent_notifications",
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_notifications",
    )
    target_id = models.CharField(max_length=26)
    target_type = models.CharField(max_length=20, choices=TargetChoices.choices)
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    message = models.CharField(max_length=150)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=[
                    "receiver",
                    "target_id",
                    "is_read",
                ],
                name="ix_receiver_target_id_is_read",
            ),
            models.Index(
                fields=["created_at"],
                name="ix_notification_created_at",
            ),
        ]
