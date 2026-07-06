from apps.core.exceptions.exception import NotFoundException
from apps.notifications.models import Notification
from apps.notifications.services import delete_notification
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationDeleteService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        create_notification(
            self.data_for_follow_noti["receiver"].id,
            self.data_for_follow_noti["sender"],
            self.data_for_follow_noti["notification_type"],
            self.data_for_follow_noti["target_id"],
        )
        self.noti = Notification.objects.get(
            receiver=self.data_for_follow_noti["receiver"],
            sender=self.data_for_follow_noti["sender"],
        )
        create_notification(
            self.data_for_follow_noti_is_read["receiver"].id,
            self.data_for_follow_noti_is_read["sender"],
            self.data_for_follow_noti_is_read["notification_type"],
            self.data_for_follow_noti_is_read["target_id"],
        )
        self.noti_2 = Notification.objects.get(
            receiver=self.data_for_follow_noti_is_read["receiver"],
            sender=self.data_for_follow_noti_is_read["sender"],
        )

    def test_delete_service(self):
        """알림 개별 삭제 처리 service 성공 테스트"""
        result = delete_notification(self.noti.id, self.user_2)
        self.assertEqual(result["notification_id"], self.noti.id)
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, id=self.noti.id).exists(),
            False,
        )
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, id=self.noti_2.id).exists(),
            True,
        )
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_2.unread_noti_count, 1)

    def test_none_noti_id_delete_service(self):
        """없은 알림 개별 삭제 처리 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            delete_notification("없는 아이디", self.user_2)

    def test_not_receiver_delete_service(self):
        """수신자가 아닌 유저가 알림 개별 삭제 처리 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            delete_notification(self.noti.id, self.user_1)
