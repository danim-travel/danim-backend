from rest_framework import serializers

from apps.users.validators import validate_password_format


class ChangePasswordRequestSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value) -> str:
        return validate_password_format(value)
