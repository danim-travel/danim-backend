from django.test import TestCase

from apps.directmessages.serializers.delete_message_serializer import (
    DeleteMessageSerializer,
)


class TestDeleteMessageSerializer(TestCase):

    def test_valid_ulids(self):
        """26자 conversation_id, message_id 검증 성공"""
        serializer = DeleteMessageSerializer(
            data={
                "conversation_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "message_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_short_conversation_id_is_invalid(self):
        """conversation_id 26자 미만 시 검증 실패"""
        serializer = DeleteMessageSerializer(
            data={
                "conversation_id": "tooshort",
                "message_id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
            }
        )
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_short_message_id_is_invalid(self):
        """message_id 26자 미만 시 검증 실패"""
        serializer = DeleteMessageSerializer(
            data={
                "conversation_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
                "message_id": "tooshort",
            }
        )
        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)

    def test_missing_fields(self):
        """필드 누락 시 검증 실패"""
        serializer = DeleteMessageSerializer(data={})
        self.assertFalse(serializer.is_valid())
