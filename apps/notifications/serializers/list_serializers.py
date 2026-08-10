from rest_framework import serializers

from apps.notifications.models import Notification
from apps.notifications.utils.create_notification import (
    SYSTEM_NOTI_TYPES,
    SYSTEM_SENDER_NAME,
)


class NotificationListSerializer(serializers.ModelSerializer):
    notification_id = serializers.CharField(source="id")
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
            "notification_type",
            "sender",
        ]

    def get_sender(self, obj):
        if not obj.sender:
            # sender=None에는 두 가지 의미가 겹쳐 있다: 탈퇴(SET_NULL)와 시스템 발신.
            # notification_type으로 갈라야 문의 답변이 "탈퇴한 유저 — 답변이
            # 등록되었습니다"로 나가는 것을 막을 수 있다.
            is_system = obj.notification_type in SYSTEM_NOTI_TYPES
            return {
                "user_id": None,
                "nickname": SYSTEM_SENDER_NAME if is_system else "탈퇴한 유저",
                "profile_img": None,
            }
        return {
            "user_id": obj.sender.id,
            "nickname": obj.sender.nickname,
            "profile_img": obj.sender.profile_img_url,
        }


class NotificationSwaggerSerializer(serializers.Serializer):
    page_size = serializers.IntegerField()


class NotificationListReadSwaggerSerializer(serializers.Serializer):
    message = serializers.CharField()
