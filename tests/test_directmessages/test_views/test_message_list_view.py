from apps.directmessages.models import Message
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestMessageListView(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.url = (
            f"/api/v1/direct-messages/conversations/{self.conversation.id}/messages"
        )
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

    def test_user1_can_get_message_list(self):
        """user1이 메시지 목록 조회 시 200 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 2)

    def test_user2_can_get_message_list(self):
        """user2가 메시지 목록 조회 시 200 반환"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_unauthenticated_request_returns_401(self):
        """비로그인 유저 요청 시 401 반환"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_non_participant_returns_404(self):
        """대화 참여자가 아닌 유저 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_invalid_conversation_id_returns_404(self):
        """존재하지 않는 대화방 id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(
            "/api/v1/direct-messages/conversations/notexistid0000000000000000/messages"
        )
        self.assertEqual(response.status_code, 404)

    def test_short_conversation_id_returns_404(self):
        """26자 미만 id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(
            "/api/v1/direct-messages/conversations/tooshort/messages"
        )
        self.assertEqual(response.status_code, 404)

    def test_long_conversation_id_returns_404(self):
        """26자 초과 id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(
            "/api/v1/direct-messages/conversations/toolongid000000000000000000/messages"
        )
        self.assertEqual(response.status_code, 404)

    def test_response_contains_next_cursor(self):
        """응답에 next 커서 필드 포함 여부 확인"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        self.assertIn("next", response.data)

    def test_message_fields_in_response(self):
        """응답 메시지 항목에 필수 필드 포함 여부 확인"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        message = response.data["results"][0]
        self.assertIn("message_id", message)
        self.assertIn("sender", message)
        self.assertIn("content", message)
        self.assertIn("img_url", message)
        self.assertIn("original_img", message)
        self.assertIn("is_deleted", message)
        self.assertIn("created_at", message)

    def test_pagination_page_size(self):
        """page_size 파라미터로 반환 개수 조절"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url + "?page_size=1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertIsNotNone(response.data["next"])

    def test_left_user_returns_404(self):
        """대화방을 나간 유저는 메시지 목록 조회 시 404 반환"""
        u1, u2 = sorted([self.user_1, self.user_2], key=lambda u: u.id)
        if self.conversation.user1_id == u1.id:
            self.conversation.user1_left_at = self.message_2.created_at
        else:
            self.conversation.user2_left_at = self.message_2.created_at
        self.conversation.save()
        self.client.force_authenticate(user=u1)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_rejoined_user_only_sees_messages_after_rejoin(self):
        """재입장한 유저는 rejoin_at 이후 메시지만 응답에 포함"""
        if self.conversation.user1_id == self.user_1.id:
            self.conversation.user1_rejoin_at = self.message_2.created_at  # type: ignore[attr-defined]
            self.conversation.save(update_fields=["user1_rejoin_at"])
            rejoining_user = self.user_1
        else:
            self.conversation.user2_rejoin_at = self.message_2.created_at  # type: ignore[attr-defined]
            self.conversation.save(update_fields=["user2_rejoin_at"])
            rejoining_user = self.user_2
        self.client.force_authenticate(user=rejoining_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["message_id"], self.message_2.id)

    def test_deleted_message_content_is_none_in_response(self):
        """삭제된 메시지는 응답에서 content가 None"""
        self.message_1.is_deleted = True
        self.message_1.save()
        self.client.force_authenticate(user=self.user_1)
        response = self.client.get(self.url)
        deleted = next(
            m for m in response.data["results"] if m["message_id"] == self.message_1.id
        )
        self.assertIsNone(deleted["content"])
