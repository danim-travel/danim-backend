from rest_framework import serializers
from apps.posts.models import Post
from apps.core.storage import s3


class PostSimpleSerializer(serializers.ModelSerializer):

    thumbnail = serializers.SerializerMethodField()
    post_id = serializers.CharField(source="id")

    class Meta:
        model = Post
        fields = ["post_id", "title", "thumbnail"]

    def get_thumbnail(self, obj: Post) -> str|None:
        if not obj.thumbnail:
            return None
        return s3.s3_svc.create_img_url(obj.thumbnail)