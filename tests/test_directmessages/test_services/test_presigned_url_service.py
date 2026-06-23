from django.utils import timezone

from apps.core.exceptions.exception import NotFoundException
from apps.directmessages.services.presigned_url_service import get_conversation_for_upload
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestGetConversationForUpload(ConversationBaseTest):

    def test_user1_passes_validation(self):
        """user1은 검증 통과 (예외 없음)"""
        get_conversation_for_upload(self.conversation.id, self.conversation.user1)

    def test_user2_passes_validation(self):
        """user2도 검증 통과 (예외 없음)"""
        get_conversation_for_upload(self.conversation.id, self.conversation.user2)

    def test_non_participant_raises_404(self):
        """대화 참여자가 아닌 유저 요청 시 404"""
        with self.assertRaises(NotFoundException):
            get_conversation_for_upload(self.conversation.id, self.user_3)

    def test_already_left_raises_404(self):
        """대화방 나간 유저 요청 시 404"""
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()
        with self.assertRaises(NotFoundException):
            get_conversation_for_upload(self.conversation.id, self.conversation.user1)

    def test_nonexistent_conversation_raises_404(self):
        """존재하지 않는 대화방 요청 시 404"""
        with self.assertRaises(NotFoundException):
            get_conversation_for_upload("01ARZ3NDEKTSV4RRFFQ69G5FAV", self.user_1)
