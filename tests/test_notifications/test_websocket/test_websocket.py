from datetime import date

from channels.testing.websocket import WebsocketCommunicator
from django.core.cache import cache
from django.test import TransactionTestCase

from apps.core.websocket.websocket_key.service import make_socket_key
from apps.follows.models import Follows
from apps.notifications.models.model import Notification
from apps.users.models.models import LoginType, User
from config.asgi import application


class TestNotificationConsumer(TransactionTestCase):

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
        self.follow = Follows.objects.create(
            follower=self.user_2,
            following=self.user_1,
        )
        assert Notification.objects.filter(
            receiver=self.user_1, sender=self.user_2
        ).exists(), "Follows 생성 시 알림이 생성되지 않음 — 시그널/훅 연결 확인 필요"
        self.socket_key = make_socket_key(self.user_1)
        self.url = f"ws/notifications"

    async def test_connect(self):
        """웹소켓 키 발급 후 웹소켓 연결 성공 테스트"""
        communicator = WebsocketCommunicator(
            application, self.url + f"?socket_key={self.socket_key}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        response = await communicator.receive_json_from()
        self.assertEqual(response["unread_count"], 1)
        self.assertFalse(cache.get(f"socket_key_{self.socket_key}"))

        await communicator.disconnect()

    async def test_non_user_id_connect(self):
        """웹소켓 키 발급 없이 웹소켓 연결 실패 테스트"""
        communicator = WebsocketCommunicator(application, self.url + f"?socket_key=")
        connected, _ = await communicator.connect()
        self.assertFalse(connected)

        await communicator.disconnect()
