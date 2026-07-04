from apps.notifications.models import Notification
from apps.notifications.services import read_all_notifications
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationReadAllService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        create_notification(
            self.data_for_follow_noti["receiver"].id,
            self.data_for_follow_noti["sender"],
            self.data_for_follow_noti["notification_type"],
            self.data_for_follow_noti["target_id"],
        )

    def test_read_all_service(self):
        """전체 알림 읽음 처리 service 성공 테스트"""
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=False).count(), 1
        )
        read_all_notifications(self.user_2)
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_2.unread_noti_count, 0)
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=False).count(), 0
        )
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=True).count(), 1
        )
