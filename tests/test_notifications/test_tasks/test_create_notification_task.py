from django.test import override_settings

from apps.notifications.models import Notification
from apps.notifications.tasks import create_notification_task
from apps.users.models import User
from tests.test_notifications.core.base import NotificationsBaseTest


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
class TestCreateNotificationTask(NotificationsBaseTest):

    def test_creates_notification_and_increments_count(self):
        """정상 실행 시 알림 생성 및 unread_noti_count 증가"""
        create_notification_task.apply(
            kwargs={
                "receiver_id": self.user_1.id,
                "sender_id": self.user_2.id,
                "noti_type": "follow",
                "target_id": self.user_2.id,
            }
        )

        self.assertEqual(
            Notification.objects.filter(receiver=self.user_1, sender=self.user_2).count(),
            1,
        )
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.unread_noti_count, 1)

    def test_missing_sender_is_skipped(self):
        """존재하지 않는 sender면 재시도 없이 스킵되고 알림이 생성되지 않는다"""
        create_notification_task.apply(
            kwargs={
                "receiver_id": self.user_1.id,
                "sender_id": "존재하지않는아이디",
                "noti_type": "follow",
                "target_id": self.user_2.id,
            }
        )

        self.assertEqual(Notification.objects.filter(receiver=self.user_1).count(), 0)
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.unread_noti_count, 0)

    def test_invalid_noti_type_is_skipped(self):
        """잘못된 noti_type이면 재시도 없이 스킵된다"""
        create_notification_task.apply(
            kwargs={
                "receiver_id": self.user_1.id,
                "sender_id": self.user_2.id,
                "noti_type": "invalid_type",
                "target_id": self.user_2.id,
            }
        )

        self.assertEqual(Notification.objects.filter(receiver=self.user_1).count(), 0)
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.unread_noti_count, 0)
