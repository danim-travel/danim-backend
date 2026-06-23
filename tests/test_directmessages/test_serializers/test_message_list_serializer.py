from unittest.mock import patch

from apps.directmessages.models import Message
from apps.directmessages.serializers.message_list_serializer import MessageListSerializer
from tests.test_core.bases.conversation_base import ConversationBaseTest


class TestMessageListSerializer(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user_1,
            content="테스트 메시지",
        )

    def _serialize(self, message):
        return MessageListSerializer(message).data

    def test_basic_fields_present(self):
        """필수 필드 존재 여부 확인"""
        data = self._serialize(self.message)
        self.assertIn("message_id", data)
        self.assertIn("sender", data)
        self.assertIn("content", data)
        self.assertIn("img_url", data)
        self.assertIn("original_img", data)
        self.assertIn("is_deleted", data)
        self.assertIn("created_at", data)

    def test_message_id_is_message_pk(self):
        """message_id가 message pk와 동일한지 확인"""
        data = self._serialize(self.message)
        self.assertEqual(data["message_id"], self.message.id)

    def test_sender_fields(self):
        """sender에 user_id, nickname, profile_img 포함 여부"""
        data = self._serialize(self.message)
        sender = data["sender"]
        self.assertIn("user_id", sender)
        self.assertIn("nickname", sender)
        self.assertIn("profile_img", sender)

    def test_deleted_message_content_is_none(self):
        """삭제된 메시지의 content는 None 반환"""
        self.message.is_deleted = True
        self.message.save()
        data = self._serialize(self.message)
        self.assertIsNone(data["content"])

    def test_deleted_message_img_url_is_none(self):
        """삭제된 메시지의 img_url은 None 반환"""
        self.message.is_deleted = True
        self.message.img_key = "some/key"
        self.message.save()
        data = self._serialize(self.message)
        self.assertIsNone(data["img_url"])

    def test_img_url_generated_from_img_key(self):
        """img_key 있으면 presigned URL 생성"""
        self.message.img_key = "images/test.jpg"
        self.message.save()
        with patch(
            "apps.directmessages.serializers.message_list_serializer.s3_svc.create_download_presigned_url"
        ) as mock_url:
            mock_url.return_value = "https://s3.example.com/presigned"
            data = self._serialize(self.message)
            self.assertEqual(data["img_url"], "https://s3.example.com/presigned")
            mock_url.assert_called_once_with("images/test.jpg")

    def test_img_url_is_none_when_no_img_key(self):
        """img_key 없으면 img_url은 None"""
        data = self._serialize(self.message)
        self.assertIsNone(data["img_url"])

    def test_deleted_message_original_img_is_none(self):
        """삭제된 메시지의 original_img는 None 반환"""
        self.message.is_deleted = True
        self.message.original_img = "test.jpg"
        self.message.save()
        data = self._serialize(self.message)
        self.assertIsNone(data["original_img"])

    def test_original_img_returned_when_not_deleted(self):
        """삭제되지 않은 메시지는 original_img 값 반환"""
        self.message.original_img = "test.jpg"
        self.message.save()
        data = self._serialize(self.message)
        self.assertEqual(data["original_img"], "test.jpg")

    def test_content_returned_when_not_deleted(self):
        """삭제되지 않은 메시지는 content 반환"""
        data = self._serialize(self.message)
        self.assertEqual(data["content"], "테스트 메시지")
