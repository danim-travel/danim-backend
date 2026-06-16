from rest_framework.exceptions import NotFound

from apps.directmessages.services.leave_conversation_service import leave_conversation
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestLeaveConversationService(ConversationBaseTest):

    def test_user1_can_leave_conversation(self):
        """user1이 대화방 나가기 성공"""
        user1 = self.conversation.user1
        leave_conversation(self.conversation.id, user1)
        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation.user1_left_at)

    def test_user2_can_leave_conversation(self):
        """user2가 대화방 나가기 성공"""
        user2 = self.conversation.user2
        leave_conversation(self.conversation.id, user2)
        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation.user2_left_at)

    def test_user1_left_at_does_not_affect_user2(self):
        """user1이 나가도 user2_left_at은 변경되지 않음"""
        user1 = self.conversation.user1
        leave_conversation(self.conversation.id, user1)
        self.conversation.refresh_from_db()
        self.assertIsNone(self.conversation.user2_left_at)

    def test_non_participant_raises_404(self):
        """대화 참여자가 아닌 유저 요청 시 404"""
        with self.assertRaises(NotFound):
            leave_conversation(self.conversation.id, self.user_3)

    def test_already_left_raises_404(self):
        """이미 나간 대화방 재요청 시 404"""
        from django.utils import timezone

        user1 = self.conversation.user1
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()
        with self.assertRaises(NotFound):
            leave_conversation(self.conversation.id, user1)
