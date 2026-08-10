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


SYSTEM_SENDER_NAME = "다님 고객센터"

# 발신 주체가 사람이 아니라 서비스인 알림. 목록 serializer는 sender=None을 "탈퇴한
# 유저"로 표시하므로(원래 SET_NULL 전용 분기), 이 집합에 속한 종류는 그 분기 대신
# SYSTEM_SENDER_NAME을 쓴다. 새 시스템 알림을 추가하면 여기에도 넣어야 하며,
# create_system_notification이 입구에서 멤버십을 강제한다.
#
# 상수를 생성 유틸이 아니라 모델 옆에 두는 이유: 표기(serializer)와 발송(utils)이
# 모두 이 값을 쓰는데, serializer가 생성 유틸을 임포트하면 의존 방향이 뒤집힌다.
SYSTEM_NOTI_TYPES = frozenset({NotificationType.INQUIRY_ANSWERED})


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
