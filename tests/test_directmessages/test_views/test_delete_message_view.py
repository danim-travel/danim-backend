from apps.directmessages.models import Message
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestDeleteMessageView(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="테스트 메시지",
        )
        self.url = f"/api/v1/direct-messages/conversations/{self.conversation.id}/messages/{self.message.id}"

    def test_sender_can_delete_returns_204(self):
        """발신자가 메시지 삭제 시 204 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)

    def test_is_deleted_set_after_delete(self):
        """삭제 후 DB에 is_deleted=True 설정 확인"""
        self.client.force_authenticate(user=self.user_1)
        self.client.delete(self.url)
        self.message.refresh_from_db()
        self.assertTrue(self.message.is_deleted)

    def test_non_sender_returns_403(self):
        """발신자가 아닌 유저 요청 시 403 반환"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 403)

    def test_non_participant_returns_404(self):
        """대화 참여자가 아닌 유저 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        """비로그인 유저 요청 시 401 반환"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_invalid_message_id_returns_404(self):
        """존재하지 않는 message_id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        url = f"/api/v1/direct-messages/conversations/{self.conversation.id}/messages/notexistid0000000000000000"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)
