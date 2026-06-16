from django.utils import timezone

from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestLeaveConversationView(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.url = f"/api/v1/direct-messages/conversations/{self.conversation.id}/"

    def test_user1_can_leave_returns_204(self):
        """user1이 대화방 나가기 성공 시 204 반환"""
        self.client.force_authenticate(user=self.conversation.user1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)

    def test_user2_can_leave_returns_204(self):
        """user2가 대화방 나가기 성공 시 204 반환"""
        self.client.force_authenticate(user=self.conversation.user2)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 204)

    def test_unauthenticated_returns_401(self):
        """비로그인 유저 요청 시 401 반환"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 401)

    def test_non_participant_returns_404(self):
        """대화 참여자가 아닌 유저 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_already_left_returns_404(self):
        """이미 나간 대화방 재요청 시 404 반환"""
        user1 = self.conversation.user1
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()
        self.client.force_authenticate(user=user1)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, 404)

    def test_short_id_returns_404(self):
        """26자 미만 id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete("/api/v1/direct-messages/conversations/tooshort/")
        self.assertEqual(response.status_code, 404)

    def test_long_id_returns_404(self):
        """26자 초과 id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(
            "/api/v1/direct-messages/conversations/toolongid000000000000000000/"
        )
        self.assertEqual(response.status_code, 404)

    def test_left_at_is_set_after_leave(self):
        """나가기 후 DB에 left_at이 설정되는지 확인"""
        user1 = self.conversation.user1
        self.client.force_authenticate(user=user1)
        self.client.delete(self.url)
        self.conversation.refresh_from_db()
        self.assertIsNotNone(self.conversation.user1_left_at)
