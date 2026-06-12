from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.directmessages.models import Conversation
from apps.users.models.models import LoginType, User


class ConversationBaseTest(TestCase):
    client: APIClient
    user_1: User
    user_2: User
    user_3: User
    conversation: Conversation
    url: str

    def setUp(self):
        self.client = APIClient()
        self.user_1 = User.objects.create(
            email="test1@example.com",
            name="test1",
            nickname="testnickname1",
            password="Password@123",
            phone_number="01012345671",
            birth_day=date(1990, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_2 = User.objects.create(
            email="test2@example.com",
            name="test2",
            nickname="testnickname2",
            password="Password@123",
            phone_number="01012345672",
            birth_day=date(1990, 1, 2),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_3 = User.objects.create(
            email="test3@example.com",
            name="test3",
            nickname="testnickname3",
            password="Password@123",
            phone_number="01012345673",
            birth_day=date(1990, 1, 3),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        self.conversation = Conversation.objects.create(user1=u1, user2=u2)
        self.url = "/api/v1/direct-messages/conversations/"
