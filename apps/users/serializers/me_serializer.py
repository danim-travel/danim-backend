from rest_framework import serializers

from apps.users.validators import validate_nickname_format


class UserUpdateRequestSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20, required=False)
    intro = serializers.CharField(max_length=100, required=False, allow_blank=True)
    key = serializers.CharField(max_length=255, required=False)

    def validate_nickname(self, value: str) -> str:
        return validate_nickname_format(value)


class UserUpdateResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    intro = serializers.CharField(allow_null=True)
    profile_img = serializers.CharField(
        source="profile_img_url", read_only=True, allow_null=True
    )
