from unittest.mock import MagicMock

from apps.directmessages.serializers.conversation_create_serializer import (
    ConversationCreateSerializer,
    ConversationResponseSerializer,
    OpponentSerializer,
)
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestConversationCreateSerializer(ConversationBaseTest):

    def test_valid_input(self):
        """유효한 receiver_id 입력 검증 성공 테스트"""
        serializer = ConversationCreateSerializer(data={"receiver_id": self.user_2.id})
        self.assertTrue(serializer.is_valid())

    def test_receiver_id_missing(self):
        """receiver_id 누락 시 검증 실패 테스트"""
        serializer = ConversationCreateSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn("receiver_id", serializer.errors)

    def test_receiver_id_too_long(self):
        """receiver_id 26자 초과 시 검증 실패 테스트"""
        serializer = ConversationCreateSerializer(data={"receiver_id": "a" * 27})
        self.assertFalse(serializer.is_valid())
        self.assertIn("receiver_id", serializer.errors)

    def test_receiver_id_empty_string(self):
        """receiver_id 빈 문자열 입력 시 검증 실패 테스트"""
        serializer = ConversationCreateSerializer(data={"receiver_id": ""})
        self.assertFalse(serializer.is_valid())
        self.assertIn("receiver_id", serializer.errors)


class TestOpponentSerializer(ConversationBaseTest):

    def test_opponent_fields(self):
        """OpponentSerializer 필드 직렬화 성공 테스트"""
        serializer = OpponentSerializer(self.user_1)
        data = serializer.data
        self.assertEqual(data["user_id"], self.user_1.id)
        self.assertEqual(data["nickname"], self.user_1.nickname)
        self.assertIn("profile_img", data)


class TestConversationResponseSerializer(ConversationBaseTest):

    def _make_request(self, user):
        request = MagicMock()
        request.user = user
        return request

    def test_response_fields(self):
        """ConversationResponseSerializer 필드 직렬화 성공 테스트"""
        serializer = ConversationResponseSerializer(
            self.conversation,
            context={"request": self._make_request(self.user_1)},
        )
        data = serializer.data
        self.assertEqual(data["conversation_id"], self.conversation.id)
        self.assertIn("opponent", data)
        self.assertIn("created_at", data)

    def test_opponent_is_user2_when_request_user_is_user1(self):
        """user1이 요청 시 상대방으로 user2를 반환하는지 테스트"""
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        serializer = ConversationResponseSerializer(
            self.conversation,
            context={"request": self._make_request(u1)},
        )
        self.assertEqual(serializer.data["opponent"]["user_id"], u2.id)

    def test_opponent_is_user1_when_request_user_is_user2(self):
        """user2가 요청 시 상대방으로 user1을 반환하는지 테스트"""
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        serializer = ConversationResponseSerializer(
            self.conversation,
            context={"request": self._make_request(u2)},
        )
        self.assertEqual(serializer.data["opponent"]["user_id"], u1.id)
