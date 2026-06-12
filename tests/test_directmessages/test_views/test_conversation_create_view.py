from apps.directmessages.models import Conversation
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestConversationCreateView(ConversationBaseTest):

    def test_create_new_conversation(self):
        """새 대화방 생성 시 201 반환 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {"receiver_id": self.user_3.id})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Conversation.objects.count(), 2)
        self.assertIn("conversation_id", response.data)
        self.assertIn("opponent", response.data)
        self.assertIn("created_at", response.data)

    def test_return_existing_conversation(self):
        """이미 존재하는 대화방 조회 시 200 반환 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {"receiver_id": self.user_2.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertEqual(response.data["conversation_id"], self.conversation.id)

    def test_unauthenticated_request(self):
        """비로그인 유저 요청 시 401 반환 테스트"""
        response = self.client.post(self.url, {"receiver_id": self.user_2.id})
        self.assertEqual(response.status_code, 401)

    def test_self_conversation_returns_400(self):
        """자기 자신과 대화방 생성 시도 시 400 반환 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {"receiver_id": self.user_1.id})
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_receiver_returns_404(self):
        """존재하지 않는 유저 id로 요청 시 404 반환 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {"receiver_id": "없는유저아이디"})
        self.assertEqual(response.status_code, 404)

    def test_missing_receiver_id_returns_400(self):
        """receiver_id 누락 시 400 반환 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 400)

    def test_bidirectional_returns_same_conversation(self):
        """반대 방향으로 요청해도 동일한 대화방 반환 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(self.url, {"receiver_id": self.user_1.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["conversation_id"], self.conversation.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_opponent_data_in_response(self):
        """응답의 opponent 필드에 user_id, nickname, profile_img 포함 여부 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(self.url, {"receiver_id": self.user_3.id})
        opponent = response.data["opponent"]
        self.assertIn("user_id", opponent)
        self.assertIn("nickname", opponent)
        self.assertIn("profile_img", opponent)
