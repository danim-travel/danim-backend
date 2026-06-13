from rest_framework import serializers


class NotificationReadSerializer(serializers.Serializer):
    """Swagger를 위한 serializer"""

    notification_id = serializers.CharField()
    is_read = serializers.BooleanField()
