from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models.models import LoginType, User


class FollowBaseTest(TestCase):
    client = APIClient()
    user_1: User
    user_2: User
    url_following_user_2: str

    def setUp(self):
        self.client = APIClient()
        self.user_1 = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day=date(1970, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_2 = User.objects.create(
            email="test_2@example.com",
            name="test_2",
            nickname="test_2_nickname",
            password="Password@123test",
            phone_number="01009002829",
            birth_day=date(1970, 1, 2),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_3 = User.objects.create(
            email="test_3@example.com",
            name="test_3",
            nickname="test_3_nickname",
            password="Password@443test",
            phone_number="01005502829",
            birth_day=date(1970, 1, 2),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.url_following_user_2 = f"/api/v1/follow/{self.user_2.id}"
