from rest_framework import serializers

from apps.users.models import User


class UserBriefSerializer(serializers.Serializer):
    user_id = serializers.CharField(source="id")
    nickname = serializers.CharField()
    profile_img = serializers.SerializerMethodField()

    def get_profile_img(self, obj: User) -> str | None:
        return obj.profile_img_url
