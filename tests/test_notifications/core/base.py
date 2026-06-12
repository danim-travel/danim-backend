from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.notifications.models.model import NotificationType, TargetChoices
from apps.users.models.models import LoginType, User


class NotificationsBaseTest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user_1 = User.objects.create(
            email="test_1@example.com",
            name="test_1",
            nickname="test_1nickname",
            password="Password_1@123",
            phone_number="01012345678",
            birth_day=date(1971, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_2 = User.objects.create(
            email="test_2@example.com",
            name="test_2",
            nickname="test_2nickname",
            password="Password_2@123",
            phone_number="01022345678",
            birth_day=date(1972, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.data_for_follow_noti = {
            "sender": self.user_1,
            "receiver": self.user_2,
            "target_id": self.user_1.id,
            "target_type": TargetChoices.USER,
            "notification_type": NotificationType.FOLLOW,
            "message": f"{self.user_1.nickname}님이 팔로우 했습니다",
            "is_read": False,
        }
        self.noti_url_list = "/api/v1/notifications"
