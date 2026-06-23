from rest_framework import serializers

from apps.core.storage.s3 import s3_svc


class BookmarkListSerializer(serializers.Serializer):
    post_id = serializers.CharField(read_only=True, source="post.id")
    thumbnail = serializers.SerializerMethodField()
    description = serializers.CharField(read_only=True, source="post.description")
    comment_count = serializers.IntegerField(read_only=True, source="post.comment_count")
    is_liked = serializers.BooleanField(read_only=True)
    like_count = serializers.IntegerField(read_only=True, source="post.like_count")

    def get_thumbnail(self, obj):
        return (
            s3_svc.create_download_presigned_url(obj.post.thumbnail)
            if obj.post.thumbnail
            else None
        )
