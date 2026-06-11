from typing import Any, cast

from rest_framework import serializers

from apps.posts.serializers.post_simple_serializer import PostSimpleSerializer
from apps.users.models import User


class ProfileResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.CharField(source="profile_img_url", allow_null=True)
    intro = serializers.CharField(allow_null=True)
    follower = serializers.IntegerField(source="follower_count")
    following = serializers.IntegerField(source="following_count")
    is_following = serializers.BooleanField()
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField()

    def get_posts(self, obj: User) -> list[dict[str, Any]]:
        qs = obj.posts.all()
        return cast(list[dict[str, Any]], PostSimpleSerializer(qs, many=True).data)
