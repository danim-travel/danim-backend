from datetime import date

from channels.db import database_sync_to_async
from channels.testing.websocket import WebsocketCommunicator
from django.test import TransactionTestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.notifications.models.model import Notification, NotificationType, TargetChoices
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
        self.noti = Notification.objects.create(
            receiver=self.user_1,
            sender=self.user_2,
            target_id=TargetChoices.POST,
            target_type="post",
            notification_type=NotificationType.COMMENT,
            message=f"{self.user_2.nickname}님이 회원님의 게시글에 댓글을 작성했습니다.",
        )
        self.url = "ws/notifications"

    async def test_connect(self):
        """토큰 인증 성공 후 웹소켓 연결 테스트"""
        communicator = WebsocketCommunicator(application, self.url)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        refresh = await database_sync_to_async(RefreshToken.for_user)(self.user_1)
        access_token = refresh.access_token
        await communicator.send_json_to({"type": "auth", "token": str(access_token)})
        response = await communicator.receive_json_from()
        self.assertEqual(response["unread_count"], 1)

        await communicator.disconnect()

    async def test_invalid_token_connect(self):
        """잘못된 토큰으로 인증 실패 테스트"""
        communicator = WebsocketCommunicator(application, self.url)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.send_json_to({"type": "auth", "token": "유효하지않은토큰"})
        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "error")

        await communicator.disconnect()
