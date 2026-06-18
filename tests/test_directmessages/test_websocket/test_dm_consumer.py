import uuid
from datetime import date

from asgiref.sync import sync_to_async
from channels.testing import WebsocketCommunicator
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils import timezone

from apps.directmessages.models import Conversation, Message
from apps.users.models.models import LoginType, User
from config.asgi import application


def make_test_socket_key(user: User) -> str:
    socket_key = str(uuid.uuid4())
    cache.set(f"socket_key_{socket_key}", user.id, timeout=30)
    return socket_key


class TestDMConsumer(TransactionTestCase):

    def setUp(self):
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
        self.base_url = f"ws/conversations/{self.conversation.id}"

    async def _make_communicator(self, user: User) -> WebsocketCommunicator:
        socket_key = await sync_to_async(make_test_socket_key)(user)
        return WebsocketCommunicator(
            application, f"{self.base_url}?socket_key={socket_key}"
        )

    async def test_auth_success(self):
        """유효한 socket_key로 정상 연결"""
        communicator = await self._make_communicator(self.user_1)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        self.assertTrue(await communicator.receive_nothing())
        await communicator.disconnect()

    async def test_auth_invalid_socket_key(self):
        """잘못된 socket_key로 연결 시 즉시 종료"""
        communicator = WebsocketCommunicator(
            application, f"{self.base_url}?socket_key=invalid-key"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_auth_no_socket_key(self):
        """socket_key 없이 연결 시 즉시 종료"""
        communicator = WebsocketCommunicator(application, self.base_url)
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        await communicator.disconnect()

    async def test_auth_non_participant(self):
        """대화 참여자가 아닌 유저 연결 시 에러 후 연결 종료"""
        communicator = await self._make_communicator(self.user_3)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "error")
        self.assertIn("대화방", response["detail"])

        await communicator.disconnect()

    async def test_auth_already_left(self):
        """대화방 나간 유저 연결 시 에러 후 연결 종료"""
        self.conversation.user1_left_at = timezone.now()
        await self.conversation.asave()

        communicator = await self._make_communicator(self.conversation.user1)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "error")

        await communicator.disconnect()

    async def test_send_message_broadcast(self):
        """send_message 시 양측에 receive_message 브로드캐스트"""
        communicator1 = await self._make_communicator(self.user_1)
        communicator2 = await self._make_communicator(self.user_2)

        await communicator1.connect()
        await communicator2.connect()

        await communicator1.send_json_to(
            {
                "type": "send_message",
                "content": "안녕하세요",
                "img_key": None,
                "original_img": None,
            }
        )

        response1 = await communicator1.receive_json_from()
        response2 = await communicator2.receive_json_from()

        self.assertEqual(response1["type"], "receive_message")
        self.assertEqual(response1["content"], "안녕하세요")
        self.assertEqual(response2["type"], "receive_message")
        self.assertEqual(response2["content"], "안녕하세요")

        await communicator1.disconnect()
        await communicator2.disconnect()

    async def test_read_receipt_on_connect(self):
        """접속 시 미읽음 메시지 읽음 처리 후 read_receipt 전송"""
        msg = await Message.objects.acreate(
            conversation=self.conversation,
            sender=self.user_1,
            content="읽어봐",
        )

        communicator = await self._make_communicator(self.user_2)
        await communicator.connect()

        response = await communicator.receive_json_from()
        self.assertEqual(response["type"], "read_receipt")
        self.assertIn(str(msg.id), response["message_ids"])

        await communicator.disconnect()

    async def test_no_read_receipt_when_no_unread(self):
        """미읽음 메시지 없으면 read_receipt 전송 안 함"""
        communicator = await self._make_communicator(self.user_1)
        await communicator.connect()

        self.assertTrue(await communicator.receive_nothing(timeout=1))

        await communicator.disconnect()
