from rest_framework import serializers


class EmailSendSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(choices=["signup", "find_password"])


class EmailVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(choices=["signup", "find_password"])
    code = serializers.RegexField(regex=r"^\d{6}$", required=True)
