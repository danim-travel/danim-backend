from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.directmessages.core.serializers import UserBriefSerializer
from apps.directmessages.models import Conversation


class LastMessageSerializer(serializers.Serializer):
    content = serializers.CharField(allow_null=True)
    img_url = serializers.CharField(allow_null=True)
    created_at = serializers.DateTimeField()


class ConversationListResponseSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(source="id")
    opponent = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    @extend_schema_field(UserBriefSerializer)
    def get_opponent(self, obj: Conversation) -> dict:
        request_user = self.context["request"].user
        opponent = obj.user2 if obj.user1_id == request_user.id else obj.user1
        return UserBriefSerializer(opponent).data

    @extend_schema_field(LastMessageSerializer)
    def get_last_message(self, obj: Conversation) -> dict | None:
        if obj.last_msg_created_at is None:  # type: ignore[attr-defined]
            return None
        is_deleted = obj.last_msg_is_deleted  # type: ignore[attr-defined]
        return {
            "content": None if is_deleted else obj.last_msg_content,  # type: ignore[attr-defined]
            "img_url": (
                s3_svc.create_download_presigned_url(obj.last_msg_img_key)  # type: ignore[attr-defined]
                if not is_deleted and obj.last_msg_img_key  # type: ignore[attr-defined]
                else None
            ),
            "created_at": obj.last_msg_created_at,  # type: ignore[attr-defined]
        }

    def get_unread_count(self, obj: Conversation) -> int:
        request_user = self.context["request"].user
        if obj.user1_id == request_user.id:
            return obj.user1_unread_count
        return obj.user2_unread_count
