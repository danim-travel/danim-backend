from rest_framework import serializers


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField(read_only=True)
