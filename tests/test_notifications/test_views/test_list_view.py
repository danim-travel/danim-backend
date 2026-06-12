from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationsListView(NotificationsBaseTest):

    def test_get_noti_list_view(self):
        """로그인한 유저의 본인의 알림 목록조회 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.noti_url_list)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_get_noti_list_view(self):
        """비로그인 유저의 본인의 알림 목록 조회 시도 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.noti_url_list)
        self.assertEqual(response.status_code, 401)
