from rest_framework import serializers

from apps.users.validators import validate_nickname_format


class KakaoSignupSerializer(serializers.Serializer):
    signup_token = serializers.CharField()
    nickname = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=20)
    birth_day = serializers.DateField()

    def validate_nickname(self, value: str) -> str:
        return validate_nickname_format(value)
