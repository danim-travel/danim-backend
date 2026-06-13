from apps.notifications.models import Notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationReadView(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.noti = Notification.objects.create(**self.data_for_follow_noti)
        self.url = f"/api/v1/notifications/{self.noti.id}"

    def test_read_view(self):
        """로그인한 유저의 개별 알림 읽음 처리 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["notification_id"], self.noti.id)
        self.assertEqual(response.data["is_read"], True)
        self.assertEqual(
            Notification.objects.filter(
                is_read=False, receiver=self.user_2, id=self.noti.id
            ).count(),
            0,
        )

    def test_unauthenticated_read_view(self):
        """비로그인 유저의 개별 알림 읽음 처리 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.url)
        self.assertEqual(response.status_code, 401)
