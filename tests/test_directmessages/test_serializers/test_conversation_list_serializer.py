from unittest.mock import MagicMock, patch

from apps.directmessages.models import Message
from apps.directmessages.serializers.conversation_list_serializer import (
    ConversationListResponseSerializer,
    LastMessageSerializer,
)
from apps.directmessages.services.conversation_list_service import get_conversation_list
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestLastMessageSerializer(ConversationBaseTest):

    def test_fields(self):
        """LastMessageSerializer 필드 직렬화 성공 테스트"""
        msg = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="테스트",
        )
        data = LastMessageSerializer(msg).data
        self.assertIn("content", data)
        self.assertIn("img_url", data)
        self.assertIn("created_at", data)


class TestConversationListResponseSerializer(ConversationBaseTest):

    def _make_request(self, user):
        request = MagicMock()
        request.user = user
        return request

    def _get_annotated_conversation(self, user):
        return get_conversation_list(user).get(id=self.conversation.id)

    def test_conversation_id_field(self):
        """conversation_id 필드 직렬화 성공 테스트"""
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertEqual(serializer.data["conversation_id"], self.conversation.id)

    def test_opponent_when_request_user_is_user1(self):
        """request_user가 user1일 때 opponent는 user2"""
        user1 = self.conversation.user1
        user2 = self.conversation.user2
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertEqual(serializer.data["opponent"]["user_id"], user2.id)

    def test_opponent_when_request_user_is_user2(self):
        """request_user가 user2일 때 opponent는 user1"""
        user1 = self.conversation.user1
        user2 = self.conversation.user2
        obj = self._get_annotated_conversation(user2)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user2)},
        )
        self.assertEqual(serializer.data["opponent"]["user_id"], user1.id)

    def test_last_message_is_none_when_no_message(self):
        """메시지 없을 때 last_message는 None"""
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertIsNone(serializer.data["last_message"])

    def test_last_message_with_content(self):
        """메시지 있을 때 content, img_url, created_at 포함"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="안녕",
        )
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        last_message = serializer.data["last_message"]
        self.assertEqual(last_message["content"], "안녕")
        self.assertIsNone(last_message["img_url"])
        self.assertIn("created_at", last_message)

    def test_last_message_with_img_key_returns_presigned_url(self):
        """img_key 있을 때 img_url에 presigned url 반환"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            img_key="some/key.jpg",
        )
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        with patch(
            "apps.directmessages.serializers.conversation_list_serializer.s3_svc.create_download_presigned_url"
        ) as mock_url:
            mock_url.return_value = "https://s3.example.com/presigned"
            serializer = ConversationListResponseSerializer(
                obj,
                context={"request": self._make_request(user1)},
            )
            last_message = serializer.data["last_message"]
        self.assertEqual(last_message["img_url"], "https://s3.example.com/presigned")

    def test_unread_count_for_user1(self):
        """request_user가 user1일 때 user1_unread_count 반환"""
        user1 = self.conversation.user1
        self.conversation.user1_unread_count = 3
        self.conversation.save()
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertEqual(serializer.data["unread_count"], 3)

    def test_unread_count_for_user2(self):
        """request_user가 user2일 때 user2_unread_count 반환"""
        user2 = self.conversation.user2
        self.conversation.user2_unread_count = 5
        self.conversation.save()
        obj = self._get_annotated_conversation(user2)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user2)},
        )
        self.assertEqual(serializer.data["unread_count"], 5)

    def test_deleted_last_message_content_is_none(self):
        """삭제된 마지막 메시지의 content는 None"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="삭제될 메시지",
            is_deleted=True,
        )
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertIsNone(serializer.data["last_message"]["content"])

    def test_deleted_last_message_img_url_is_none(self):
        """삭제된 마지막 메시지의 img_url은 None"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            img_key="some/key.jpg",
            is_deleted=True,
        )
        user1 = self.conversation.user1
        obj = self._get_annotated_conversation(user1)
        serializer = ConversationListResponseSerializer(
            obj,
            context={"request": self._make_request(user1)},
        )
        self.assertIsNone(serializer.data["last_message"]["img_url"])
