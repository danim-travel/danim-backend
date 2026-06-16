from datetime import date

from channels.db import database_sync_to_async
from channels.testing.websocket import WebsocketCommunicator
from django.core.cache import cache
from django.test import TransactionTestCase

from apps.notifications.utils.create_notification import push_channel_noti
from apps.users.models.models import LoginType, User
from config.asgi import application


class TestPushChannel(TransactionTestCase):

    def setUp(self):
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
        self.ws_url = f"ws/notifications/{self.user_1.id}"

    def tearDown(self):
        cache.delete(f"user_{self.user_1.id}_unread_count")
        super().tearDown()

    async def test_push_channel(self):
        """새로운 알림 생성시 클라이언트단에 push 테스트"""
        communicator = WebsocketCommunicator(application, self.ws_url)
        connected, _ = await communicator.connect()
        await communicator.receive_json_from()

        await database_sync_to_async(push_channel_noti)(str(self.user_1.id))
        response = await communicator.receive_json_from()
        self.assertEqual(response["unread_count"], 0)

        await communicator.disconnect()
