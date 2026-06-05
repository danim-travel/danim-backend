from rest_framework import serializers


class UserSearchResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField(source="id")
    nickname = serializers.CharField()
    profile_img = serializers.CharField(source="profile_img_url", allow_null=True)
