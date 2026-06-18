from rest_framework import serializers


class SocketKeySerializer(serializers.Serializer):
    socket_key = serializers.UUIDField()
