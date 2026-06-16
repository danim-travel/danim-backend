import datetime

from django.utils import timezone

from apps.directmessages.models import Conversation
from apps.directmessages.services.conversation_list_service import get_conversation_list
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestConversationListService(ConversationBaseTest):

    def test_returns_conversation_where_user_is_user1(self):
        """user1로 참여한 대화방 반환 테스트"""
        user1 = self.conversation.user1
        result = get_conversation_list(user1)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().id, self.conversation.id)

    def test_returns_conversation_where_user_is_user2(self):
        """user2로 참여한 대화방 반환 테스트"""
        user2 = self.conversation.user2
        result = get_conversation_list(user2)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().id, self.conversation.id)

    def test_returns_empty_queryset_when_no_conversation(self):
        """대화방 없는 유저 요청 시 빈 QuerySet 반환 테스트"""
        result = get_conversation_list(self.user_3)
        self.assertEqual(result.count(), 0)

    def test_ordered_by_last_message_at_desc(self):
        """last_message_at 내림차순 정렬 테스트"""
        u1, u3 = sorted([self.user_1, self.user_3], key=lambda u: u.id)
        conv2 = Conversation.objects.create(user1=u1, user2=u3)
        now = timezone.now()
        self.conversation.last_message_at = now - datetime.timedelta(hours=1)
        self.conversation.save()
        conv2.last_message_at = now
        conv2.save()
        result = get_conversation_list(self.user_1)
        self.assertEqual(result.first().id, conv2.id)

    def test_null_last_message_at_appears_last(self):
        """last_message_at이 null인 대화방은 맨 아래에 위치하는 테스트"""
        u1, u3 = sorted([self.user_1, self.user_3], key=lambda u: u.id)
        conv2 = Conversation.objects.create(user1=u1, user2=u3)
        self.conversation.last_message_at = timezone.now()
        self.conversation.save()
        result = get_conversation_list(self.user_1)
        self.assertEqual(result.first().id, self.conversation.id)
        self.assertEqual(result.last().id, conv2.id)

    def test_does_not_return_other_users_conversation(self):
        """자신이 참여하지 않은 대화방은 반환하지 않는 테스트"""
        result = get_conversation_list(self.user_3)
        ids = list(result.values_list("id", flat=True))
        self.assertNotIn(self.conversation.id, ids)

    def test_left_at_excludes_conversation_for_user1(self):
        """user1이 나간 대화방은 목록에서 제외"""
        user1 = self.conversation.user1
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()
        result = get_conversation_list(user1)
        self.assertEqual(result.count(), 0)

    def test_left_at_excludes_conversation_for_user2(self):
        """user2가 나간 대화방은 목록에서 제외"""
        user2 = self.conversation.user2
        self.conversation.user2_left_at = timezone.now()
        self.conversation.save()
        result = get_conversation_list(user2)
        self.assertEqual(result.count(), 0)

    def test_opponent_left_at_does_not_affect_my_list(self):
        """상대방이 나간 대화방은 내 목록에서 유지"""
        user1 = self.conversation.user1
        self.conversation.user2_left_at = timezone.now()
        self.conversation.save()
        result = get_conversation_list(user1)
        self.assertEqual(result.count(), 1)
