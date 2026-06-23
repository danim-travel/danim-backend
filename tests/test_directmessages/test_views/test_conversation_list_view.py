import datetime
from unittest.mock import patch

from django.utils import timezone

from apps.directmessages.models import Conversation, Message
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestConversationListView(ConversationBaseTest):

    def test_unauthenticated_returns_401(self):
        """비로그인 유저 요청 시 401 반환"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        """인증된 유저 요청 시 200 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_returns_results_key(self):
        """응답에 results 키 포함 여부 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertIn("results", response.data)

    def test_no_conversation_returns_empty_list(self):
        """대화방 없는 유저 요청 시 빈 배열 반환"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["results"], [])

    def test_response_fields(self):
        """응답 필드 구조 확인"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        item = response.data["results"][0]
        self.assertIn("conversation_id", item)
        self.assertIn("opponent", item)
        self.assertIn("last_message", item)
        self.assertIn("unread_count", item)
        opponent = item["opponent"]
        self.assertIn("user_id", opponent)
        self.assertIn("nickname", opponent)
        self.assertIn("profile_img", opponent)

    def test_opponent_when_request_user_is_user1(self):
        """request_user가 user1일 때 opponent는 user2"""
        user1 = self.conversation.user1
        user2 = self.conversation.user2
        self.client.force_authenticate(user=user1)
        response = self.client.get(self.url)
        opponent = response.data["results"][0]["opponent"]
        self.assertEqual(opponent["user_id"], user2.id)

    def test_opponent_when_request_user_is_user2(self):
        """request_user가 user2일 때 opponent는 user1"""
        user1 = self.conversation.user1
        user2 = self.conversation.user2
        self.client.force_authenticate(user=user2)
        response = self.client.get(self.url)
        opponent = response.data["results"][0]["opponent"]
        self.assertEqual(opponent["user_id"], user1.id)

    def test_last_message_is_none_when_no_message(self):
        """메시지 없을 때 last_message는 None"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertIsNone(response.data["results"][0]["last_message"])

    def test_last_message_with_content(self):
        """메시지 있을 때 content, img_url, created_at 포함"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="안녕하세요",
        )
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        last_message = response.data["results"][0]["last_message"]
        self.assertEqual(last_message["content"], "안녕하세요")
        self.assertIsNone(last_message["img_url"])
        self.assertIn("created_at", last_message)

    def test_last_message_with_img_key_returns_presigned_url(self):
        """img_key 있을 때 img_url에 presigned url 반환"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            img_key="some/key.jpg",
        )
        with patch(
            "apps.directmessages.serializers.conversation_list_serializer.s3_svc.create_download_presigned_url"
        ) as mock_url:
            mock_url.return_value = "https://s3.example.com/presigned"
            self.client.force_authenticate(user=self.user_1)
            response = self.client.get(self.url)
        last_message = response.data["results"][0]["last_message"]
        self.assertEqual(last_message["img_url"], "https://s3.example.com/presigned")

    def test_unread_count_for_user1(self):
        """request_user가 user1일 때 user1_unread_count 반환"""
        user1 = self.conversation.user1
        self.conversation.user1_unread_count = 3
        self.conversation.save()
        self.client.force_authenticate(user=user1)
        response = self.client.get(self.url)
        self.assertEqual(response.data["results"][0]["unread_count"], 3)

    def test_unread_count_for_user2(self):
        """request_user가 user2일 때 user2_unread_count 반환"""
        user2 = self.conversation.user2
        self.conversation.user2_unread_count = 5
        self.conversation.save()
        self.client.force_authenticate(user=user2)
        response = self.client.get(self.url)
        self.assertEqual(response.data["results"][0]["unread_count"], 5)

    def test_left_at_hides_conversation_in_list(self):
        """나간 대화방은 목록에서 제외"""
        from django.utils import timezone

        user1 = self.conversation.user1
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()
        self.client.force_authenticate(user=user1)
        response = self.client.get(self.url)
        self.assertEqual(response.data["results"], [])

    def test_opponent_left_does_not_hide_my_conversation(self):
        """상대방이 나간 대화방은 내 목록에서 유지"""
        from django.utils import timezone

        user1 = self.conversation.user1
        self.conversation.user2_left_at = timezone.now()
        self.conversation.save()
        self.client.force_authenticate(user=user1)
        response = self.client.get(self.url)
        self.assertEqual(len(response.data["results"]), 1)

    def test_deleted_last_message_content_is_none_in_response(self):
        """삭제된 마지막 메시지는 content가 None"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="삭제됨",
            is_deleted=True,
        )
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertIsNone(response.data["results"][0]["last_message"]["content"])

    def test_ordering_by_last_message_at(self):
        """last_message_at 내림차순 정렬 확인"""
        u1, u3 = sorted([self.user_1, self.user_3], key=lambda u: u.id)
        conv2 = Conversation.objects.create(user1=u1, user2=u3)
        now = timezone.now()
        self.conversation.last_message_at = now - datetime.timedelta(hours=1)
        self.conversation.save()
        conv2.last_message_at = now
        conv2.save()
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["conversation_id"], conv2.id)
