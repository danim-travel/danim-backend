from apps.notifications.models import Notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationModel(NotificationsBaseTest):

    def test_create_notifications(self):
        """notification 객체 저장 성공 model 성공 테스트"""
        new_notification = Notification.objects.create(**self.data_for_follow_noti)
        self.assertEqual(new_notification.sender, self.user_1)
        self.assertEqual(new_notification.receiver, self.user_2)
        self.assertEqual(new_notification.target_id, self.user_1.id)
        self.assertEqual(new_notification.target_type, "user")
        self.assertEqual(new_notification.notification_type, "follow")
        self.assertEqual(new_notification.message, self.data_for_follow_noti["message"])
        self.assertFalse(new_notification.is_read)
        self.assertEqual(Notification.objects.count(), 1)

    def test_sender_null_true(self):
        """알림을 생성하고 이후 sender가 탈퇴했을 때 SET_NULL 적용 model 테스트"""
        new_notification = Notification.objects.create(**self.data_for_follow_noti)
        self.user_1.delete()
        new_notification.refresh_from_db()
        self.assertEqual(Notification.objects.count(), 1)
        self.assertIsNone(new_notification.sender)

    def test_receiver_null_cascade(self):
        """수신자 탈퇴시 CASCADE 적용 model 테스트"""
        Notification.objects.create(**self.data_for_follow_noti)
        self.user_2.delete()
        self.assertEqual(Notification.objects.count(), 0)
