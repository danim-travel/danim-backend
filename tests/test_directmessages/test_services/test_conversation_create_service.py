from apps.core.exceptions.exception import NotFoundException, ValidationException
from apps.directmessages.models import Conversation
from apps.directmessages.services.conversation_create_service import (
    get_or_create_conversation,
)
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestConversationCreateService(ConversationBaseTest):

    def test_create_new_conversation(self):
        """새 대화방 생성 시 (conversation, True) 반환 테스트"""
        conversation, created = get_or_create_conversation(self.user_3.id, self.user_1)
        self.assertTrue(created)
        self.assertIsInstance(conversation, Conversation)
        self.assertEqual(Conversation.objects.count(), 2)

    def test_return_existing_conversation(self):
        """이미 존재하는 대화방 조회 시 (conversation, False) 반환 테스트"""
        conversation, created = get_or_create_conversation(self.user_2.id, self.user_1)
        self.assertFalse(created)
        self.assertEqual(conversation.id, self.conversation.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_self_conversation_raises_validation_exception(self):
        """자기 자신과 대화방 생성 시도 시 ValidationException 발생 테스트"""
        with self.assertRaises(ValidationException):
            get_or_create_conversation(self.user_1.id, self.user_1)

    def test_nonexistent_user_raises_not_found_exception(self):
        """존재하지 않는 유저 id로 시도 시 NotFoundException 발생 테스트"""
        with self.assertRaises(NotFoundException):
            get_or_create_conversation("없는유저아이디", self.user_1)

    def test_bidirectional_returns_same_conversation(self):
        """user_2가 user_1에게 요청해도 동일한 대화방 반환 테스트"""
        conversation, created = get_or_create_conversation(self.user_1.id, self.user_2)
        self.assertFalse(created)
        self.assertEqual(conversation.id, self.conversation.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_user_order_is_always_sorted(self):
        """user1_id < user2_id 정렬이 항상 보장되는지 테스트"""
        get_or_create_conversation(self.user_3.id, self.user_1)
        conversation = Conversation.objects.get(
            **{
                k: v
                for k, v in zip(
                    ["user1", "user2"],
                    sorted([self.user_1, self.user_3], key=lambda u: u.id),
                )
            }
        )
        self.assertLessEqual(conversation.user1_id, conversation.user2_id)
