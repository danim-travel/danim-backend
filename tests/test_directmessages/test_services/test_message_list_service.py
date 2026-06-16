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

    def test_short_conversation_id_raises_404_without_db_query(self):
        """26자 미만 id는 DB 조회 없이 즉시 404 반환"""
        with self.assertNumQueries(0):
            with self.assertRaises(NotFound):
                get_message_list("tooshort", self.user_1)

    def test_long_conversation_id_raises_404_without_db_query(self):
        """26자 초과 id는 DB 조회 없이 즉시 404 반환"""
        with self.assertNumQueries(0):
            with self.assertRaises(NotFound):
                get_message_list("toolongid000000000000000000", self.user_1)

    def test_messages_filtered_by_left_at(self):
        """유저가 나간 시각 이후 메시지는 조회되지 않음"""
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        left_at = (
            self.message_2.created_at
        )  # 결정적 시각 - timezone.now()의 타이밍 이슈 방지
        if self.conversation.user1_id == u1.id:
            self.conversation.user1_left_at = left_at
        else:
            self.conversation.user2_left_at = left_at
        self.conversation.save()

        Message.objects.create(
            conversation=self.conversation,
            sender=u2,
            content="나간 이후 메시지",
        )

        qs = get_message_list(self.conversation.id, u1)
        self.assertEqual(qs.count(), 2)

    def test_select_related_sender(self):
        """select_related로 sender N+1 방지 - 쿼리셋 평가 1회(JOIN 포함) 후 sender 접근 시 추가 쿼리 없음"""
        qs = get_message_list(self.conversation.id, self.user_1)
        with self.assertNumQueries(1):  # SELECT messages JOIN users 단 1회
            messages = list(qs)
        with self.assertNumQueries(0):
            for msg in messages:
                _ = msg.sender.nickname
