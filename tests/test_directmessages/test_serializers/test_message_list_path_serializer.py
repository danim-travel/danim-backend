from django.test import TestCase

from apps.directmessages.serializers.message_list_serializer import (
    MessageListPathSerializer,
)


class TestMessageListPathSerializer(TestCase):

    def test_valid_ulid(self):
        """26자 conversation_id 검증 성공"""
        serializer = MessageListPathSerializer(
            data={"conversation_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"}
        )
        self.assertTrue(serializer.is_valid())

    def test_short_id_is_invalid(self):
        """26자 미만 id 검증 실패"""
        serializer = MessageListPathSerializer(data={"conversation_id": "tooshort"})
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_long_id_is_invalid(self):
        """26자 초과 id 검증 실패"""
        serializer = MessageListPathSerializer(
            data={"conversation_id": "toolongid000000000000000000"}
        )
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_missing_conversation_id(self):
        """conversation_id 누락 시 검증 실패"""
        serializer = MessageListPathSerializer(data={})
        self.assertFalse(serializer.is_valid())
