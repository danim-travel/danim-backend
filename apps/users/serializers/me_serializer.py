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


class UserInfoResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField(source="id", read_only=True)
    nickname = serializers.CharField(read_only=True)
    profile_img = serializers.CharField(
        source="profile_img_url", read_only=True, allow_null=True
    )
    email = serializers.EmailField(read_only=True)
    birth_day = serializers.DateField(read_only=True)
    name = serializers.CharField(read_only=True)
    phone_number = serializers.CharField(read_only=True, allow_null=True)


class UserDeleteRequestSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
    )
