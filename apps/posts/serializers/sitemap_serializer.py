from rest_framework import serializers

from apps.posts.models import Post


class SitemapSerializer(serializers.ModelSerializer):
    post_id = serializers.CharField(source="id")
    updated_at = serializers.DateTimeField(format="%Y-%m-%d")

    class Meta:
        model = Post
        fields = [
            "post_id",
            "updated_at",
        ]
