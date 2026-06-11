from rest_framework import serializers

from apps.notifications.models import Notification


class NotificationListSerializer(serializers.ModelSerializer):
    notification_id = serializers.IntegerField(source="id")
    sender = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "notification_id",
            "message",
            "created_at",
            "target_id",
            "target_type",
            "is_read",
            "sender",
        ]

    def get_sender(self, obj):
        if not obj.sender:
            return {
                "id": None,
                "nickname": "탈퇴한 유저",
                "profile_img": None,
            }
        return {
            "id": obj.sender.id,
            "nickname": obj.sender.nickname,
            "profile_img": obj.sender.profile_img_url,
        }
