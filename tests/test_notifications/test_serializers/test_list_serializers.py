from django.utils.dateparse import parse_datetime

from apps.notifications.models.model import Notification, NotificationType, TargetChoices
from apps.notifications.serializers import NotificationListSerializer
from tests.test_notifications.core.base import NotificationsBaseTest


class TestNotificationListSerializer(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.noti_1 = Notification.objects.create(**self.data_for_follow_noti)

    def test_list_serializer(self):
        """알림 목록 조회 응답 serializer 성공 테스트"""
        serializer = NotificationListSerializer(self.noti_1)
        self.assertEqual(serializer.data["sender"].get("user_id"), self.user_1.id)
        self.assertEqual(serializer.data["sender"].get("nickname"), self.user_1.nickname)
        self.assertEqual(
            serializer.data["sender"].get("profile_img"), self.user_1.profile_img_url
        )
        self.assertEqual(serializer.data["notification_id"], self.noti_1.id)
        self.assertEqual(serializer.data["target_id"], self.user_1.id)
        self.assertEqual(serializer.data["target_type"], TargetChoices.USER)
        self.assertEqual(serializer.data["notification_type"], NotificationType.FOLLOW)
        self.assertEqual(serializer.data["message"], self.data_for_follow_noti["message"])
        self.assertFalse(serializer.data["is_read"])
        self.assertEqual(
            parse_datetime(serializer.data["created_at"]), self.noti_1.created_at
        )
