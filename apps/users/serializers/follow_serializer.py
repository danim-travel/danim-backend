from rest_framework import serializers


class FollowerResponseSerializer(serializers.Serializer):
    user_id = serializers.CharField(source="follower.id")
    nickname = serializers.CharField(source="follower.nickname")
    profile_img = serializers.CharField(
        source="follower.profile_img_url", allow_null=True
    )
    is_following = serializers.BooleanField()
