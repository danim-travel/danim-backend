from apps.notifications.models import Notification
from apps.notifications.services import delete_all_notifications
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationDeleteAllService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        create_notification(
            self.data_for_follow_noti["receiver"].id,
            self.data_for_follow_noti["sender"],
            self.data_for_follow_noti["notification_type"],
            self.data_for_follow_noti["target_id"],
        )

    def test_delete_all_service(self):
        """전체 알림 삭제 처리 service 성공 테스트"""
        self.assertEqual(Notification.objects.count(), 1)
        delete_all_notifications(self.user_2)
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_2.unread_noti_count, 0)
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)

    def test_not_receiver_delete_all_service(self):
        """알림이 없는 유저가 전체 알림 삭제 처리 service 성공 테스트"""
        self.assertEqual(Notification.objects.count(), 1)
        delete_all_notifications(self.user_1)
        self.user_1.refresh_from_db()
        self.assertEqual(self.user_1.unread_noti_count, 0)
        self.assertEqual(Notification.objects.filter(receiver=self.user_1).count(), 0)
        self.assertEqual(Notification.objects.all().count(), 1)
