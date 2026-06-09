from typing import Any, cast

from rest_framework import serializers

from apps.core.storage import s3
from apps.posts.models import Post
from apps.users.models import User


class PostSimpleSerializer(serializers.ModelSerializer):
    """post 앱 올라오면 apps/posts/serializer 로 옮기기"""

    thumbnail = serializers.SerializerMethodField()
    post_id = serializers.CharField(source="id")

    class Meta:
        model = Post
        fields = ["post_id", "title", "thumbnail"]

    def get_thumbnail(self, obj: Post) -> str:
        return s3.s3_svc.create_img_url(obj.thumbnail)


class ProfileResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.SerializerMethodField()
    intro = serializers.CharField(allow_null=True)
    follower = serializers.IntegerField()
    following = serializers.IntegerField()
    is_following = serializers.BooleanField()
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField()

    def get_profile_img(self, obj: User) -> str | None:
        """프로필 이미지를 가져오는 검증"""
        if not obj.profile_img:
            return None
        return s3.s3_svc.create_img_url(obj.profile_img)

    def get_posts(self, obj: User) -> list[dict[str, Any]]:
        qs = obj.posts.all()
        return cast(list[dict[str, Any]], PostSimpleSerializer(qs, many=True).data)
