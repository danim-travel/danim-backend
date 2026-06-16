from rest_framework.exceptions import NotFound, PermissionDenied

from apps.directmessages.models import Message
from apps.directmessages.services.delete_message_service import delete_message
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestDeleteMessageService(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="테스트 메시지",
        )

    def test_sender_can_delete_message(self):
        """메시지 발신자가 삭제 성공 시 is_deleted=True"""
        delete_message(self.conversation.id, self.message.id, self.user_1)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_deleted)

    def test_non_sender_raises_403(self):
        """발신자가 아닌 유저 요청 시 403"""
        with self.assertRaises(PermissionDenied):
            delete_message(self.conversation.id, self.message.id, self.user_2)

    def test_non_participant_raises_404(self):
        """대화 참여자가 아닌 유저 요청 시 404"""
        with self.assertRaises(NotFound):
            delete_message(self.conversation.id, self.message.id, self.user_3)

    def test_invalid_conversation_id_raises_404(self):
        """존재하지 않는 대화방 id 요청 시 404"""
        with self.assertRaises(NotFound):
            delete_message("notexistid0000000000000000", self.message.id, self.user_1)

    def test_invalid_message_id_raises_404(self):
        """존재하지 않는 메시지 id 요청 시 404"""
        with self.assertRaises(NotFound):
            delete_message(
                self.conversation.id, "notexistid0000000000000000", self.user_1
            )

    def test_message_in_other_conversation_raises_404(self):
        """다른 대화방의 메시지 삭제 시도 시 404"""
        u1, u3 = sorted([self.user_1, self.user_3], key=lambda u: u.id)
        other_conversation = type(self.conversation).objects.create(user1=u1, user2=u3)
        other_message = Message.objects.create(
            conversation=other_conversation,
            sender=self.user_1,
            content="다른 대화방 메시지",
        )
        with self.assertRaises(NotFound):
            delete_message(self.conversation.id, other_message.id, self.user_1)
