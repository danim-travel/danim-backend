from apps.notifications.models import Notification
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationDeleteView(NotificationsBaseTest):

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
        self.url = f"/api/v1/notifications/{self.noti.id}"

    def test_delete_view(self):
        """로그인한 유저의 알림 개별 삭제 처리 view 성공 테스트 후 같은 요청 재시도 후 실패 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notification_id"], self.noti.id)
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, id=self.noti.id).exists(),
            False,
        )
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_delete_view(self):
        """비로그인 유저의 알림 개별 삭제 처리 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, id=self.noti.id).exists(),
            True,
        )

    def test_not_receiver_delete_view(self):
        """수신자가 아닌 유저가 다른 유저의 알림 개별 삭제 처리 view 실패 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            Notification.objects.filter(receiver=self.user_2, id=self.noti.id).exists(),
            True,
        )
