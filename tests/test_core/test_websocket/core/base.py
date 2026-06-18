from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.users.models import LoginType, User


class SocketBaseTest(TestCase):

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
        self.url = "/api/v1/websocket-key"
