from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.directmessages.core.serializers import UserBriefSerializer
from apps.directmessages.models import Message


class MessageListSerializer(serializers.Serializer):
    message_id = serializers.CharField(source="id")
    sender = UserBriefSerializer()
    content = serializers.SerializerMethodField()
    img_url = serializers.SerializerMethodField()
    original_img = serializers.SerializerMethodField()
    is_deleted = serializers.BooleanField()
    created_at = serializers.DateTimeField()

    def get_content(self, obj: Message) -> str | None:
        return None if obj.is_deleted else obj.content

    def get_img_url(self, obj: Message) -> str | None:
        if obj.is_deleted or not obj.img_key:
            return None
        return s3_svc.create_download_presigned_url(obj.img_key)

    def get_original_img(self, obj: Message) -> str | None:
        return None if obj.is_deleted else obj.original_img
