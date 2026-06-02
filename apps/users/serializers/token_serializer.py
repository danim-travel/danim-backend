from rest_framework import serializers


class TokenRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField(read_only=True)
