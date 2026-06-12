from apps.notifications.models import Notification
from apps.notifications.services import get_notification_list
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationListService(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.notification = Notification.objects.create(**self.data_for_follow_noti)

    def test_list_service(self):
        """알림 전체 목록 조회 service 성공 테스트"""
        queryset = get_notification_list(self.user_2)
        self.assertEqual(queryset.count(), 1)
        self.assertEqual(queryset[0].receiver, self.user_2)
        self.assertEqual(queryset[0].sender, self.user_1)
