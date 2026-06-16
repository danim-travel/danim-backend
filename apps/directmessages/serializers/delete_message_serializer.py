from rest_framework import serializers

from apps.core.utils.validators import validate_ulid


class DeleteMessageSerializer(serializers.Serializer):
    conversation_id = serializers.CharField()
    message_id = serializers.CharField()

    def validate_conversation_id(self, value: str) -> str:
        validate_ulid(value)
        return value

    def validate_message_id(self, value: str) -> str:
        validate_ulid(value)
        return value
