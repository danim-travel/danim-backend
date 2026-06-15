from rest_framework import serializers
from apps.users.validators import validate_password_format

class ResetPasswordRequestSerializer(serializers.Serializer):
    email_token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self,value:str)->str:
        return validate_password_format(value)