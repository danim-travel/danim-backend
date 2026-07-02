from apps.core.exceptions.exception import NotFoundException
from apps.notifications.models import Notification
from apps.notifications.services import read_notification
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationReadService(NotificationsBaseTest):

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

    def test_read_service(self):
        """개별 알림 읽음 처리 service 성공 테스트"""
        result = read_notification(self.noti.id, self.user_2)
        self.assertEqual(result["is_read"], True)
        self.assertEqual(result["notification_id"], self.noti.id)

    def test_non_noti_id_read_service(self):
        """없는 게시글 개별 읽음 처리 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            read_notification("없는아이디", self.user_2)

    def test_no_receiver_user_read_service(self):
        """수신자가 아닌 유저의 개별 알림 읽음 처리 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            read_notification(self.noti.id, self.user_1)
