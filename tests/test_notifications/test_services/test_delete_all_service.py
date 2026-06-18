from apps.notifications.models import Notification
from apps.notifications.services import delete_all_notifications
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationDeleteAllService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.noti = Notification.objects.create(**self.data_for_follow_noti)
        self.noti_2 = Notification.objects.create(**self.data_for_follow_noti_is_read)

    def test_delete_all_service(self):
        """전체 알림 삭제 처리 service 성공 테스트"""
        self.assertEqual(Notification.objects.count(), 2)
        delete_all_notifications(self.user_2)
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)

    def test_not_receiver_delete_all_service(self):
        """알림이 없는 유저가 전체 알림 삭제 처리 service 성공 테스트"""
        self.assertEqual(Notification.objects.count(), 2)
        delete_all_notifications(self.user_1)
        self.assertEqual(Notification.objects.filter(receiver=self.user_1).count(), 0)
        self.assertEqual(Notification.objects.all().count(), 2)
