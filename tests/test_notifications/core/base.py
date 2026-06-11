from apps.notifications.models.model import NotificationType, TargetChoices
from tests.core.base import BaseUser


class NotificationsBaseTest(BaseUser):

    def setUp(self):
        super().setUp()
        self.data_for_follow_noti = {
            "sender": self.user_1,
            "receiver": self.user_2,
            "target_id": self.user_1.id,
            "target_type": TargetChoices.USER,
            "notification_type": NotificationType.FOLLOW,
            "message": f"{self.user_1.nickname}님이 팔로우 했습니다",
            "is_read": False,
        }
