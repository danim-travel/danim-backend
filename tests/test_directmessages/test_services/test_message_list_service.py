from django.utils import timezone
from rest_framework.exceptions import NotFound

from apps.directmessages.models import Message
from apps.directmessages.services.message_list_service import get_message_list
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestMessageListService(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.message_1 = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="첫 번째 메시지",
        )
        self.message_2 = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_2,
            content="두 번째 메시지",
        )

    def test_user1_can_get_messages(self):
        """user1이 메시지 목록 조회 가능"""
        qs = get_message_list(self.conversation.id, self.user_1)
        self.assertEqual(qs.count(), 2)

    def test_user2_can_get_messages(self):
        """user2가 메시지 목록 조회 가능"""
        qs = get_message_list(self.conversation.id, self.user_2)
        self.assertEqual(qs.count(), 2)

    def test_non_participant_raises_404(self):
        """대화 참여자가 아닌 유저 요청 시 404 반환"""
        with self.assertRaises(NotFound):
            get_message_list(self.conversation.id, self.user_3)

    def test_invalid_conversation_id_raises_404(self):
        """존재하지 않는 대화방 id 요청 시 404 반환"""
        with self.assertRaises(NotFound):
            get_message_list("notexistid0000000000000000", self.user_1)

    def test_left_user_raises_404(self):
        """대화방을 나간 유저는 메시지 목록 조회 시 404"""
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        if self.conversation.user1_id == u1.id:
            self.conversation.user1_left_at = self.message_2.created_at
        else:
            self.conversation.user2_left_at = self.message_2.created_at
        self.conversation.save()
        with self.assertRaises(NotFound):
            get_message_list(self.conversation.id, u1)

    def test_rejoined_user_only_sees_messages_after_rejoin(self):
        """재입장한 유저는 rejoin_at 이후 메시지만 조회 가능"""
        if self.conversation.user1_id == self.user_1.id:
            self.conversation.user1_rejoin_at = self.message_2.created_at
            self.conversation.save(update_fields=["user1_rejoin_at"])
            rejoining_user = self.user_1
        else:
            self.conversation.user2_rejoin_at = self.message_2.created_at
            self.conversation.save(update_fields=["user2_rejoin_at"])
            rejoining_user = self.user_2
        qs = get_message_list(self.conversation.id, rejoining_user)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().id, self.message_2.id)

    def test_select_related_sender(self):
        """select_related로 sender N+1 방지 - 쿼리셋 평가 1회(JOIN 포함) 후 sender 접근 시 추가 쿼리 없음"""
        qs = get_message_list(self.conversation.id, self.user_1)
        with self.assertNumQueries(1):  # SELECT messages JOIN users 단 1회
            messages = list(qs)
        with self.assertNumQueries(0):
            for msg in messages:
                _ = msg.sender.nickname
