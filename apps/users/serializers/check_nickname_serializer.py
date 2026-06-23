from rest_framework import serializers

from apps.users.validators import validate_nickname_format


class CheckNicknameSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20)

    def validate_nickname(self, value: str) -> str:
        return validate_nickname_format(value)
