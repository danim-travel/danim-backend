from apps.notifications.models import Notification
from apps.notifications.utils.create_notification import create_notification
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationDeleteAllView(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        create_notification(
            self.data_for_follow_noti["receiver"].id,
            self.data_for_follow_noti["sender"],
            self.data_for_follow_noti["notification_type"],
            self.data_for_follow_noti["target_id"],
        )

    def test_delete_all_view(self):
        """로그인한 유저의 알림 전체 삭제 처리 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.noti_url_list)
        self.assertEqual(Notification.objects.count(), 0)
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_2.unread_noti_count, 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "모든 알림이 삭제 처리 되었습니다.")

    def test_no_noti_user_delete_all_view(self):
        """알림이 없는 유저의 전체 알림 삭제 처리 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.noti_url_list)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "모든 알림이 삭제 처리 되었습니다.")

    def test_unauthorized_delete_all_view(self):
        """비로그인 유저의 알림 전체 삭제 처리 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.noti_url_list)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(Notification.objects.count(), 1)
