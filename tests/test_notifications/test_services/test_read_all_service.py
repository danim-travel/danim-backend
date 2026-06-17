from apps.notifications.models import Notification
from apps.notifications.services import read_all_notifications
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationReadAllService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.noti = Notification.objects.create(**self.data_for_follow_noti)
        self.noti_is_read = Notification.objects.create(
            **self.data_for_follow_noti_is_read
        )

    def test_read_all_service(self):
        """전체 알림 읽음 처리 service 성공 테스트"""
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=False).count(), 1
        )
        read_all_notifications(self.user_2)
        self.noti.refresh_from_db()
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=False).count(), 0
        )
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, is_read=True).count(), 2
        )
