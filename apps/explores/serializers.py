from rest_framework import serializers

from apps.posts.models import Post


class ExploreQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, default=None, allow_blank=True)
    cursor = serializers.CharField(required=False, default=None, allow_blank=True)
    page_size = serializers.IntegerField(required=False, default=10)
    seed = serializers.IntegerField(required=False, default=None)

    def validate_page_size(self, value):
        if value != 10:
            return 10
        return value


class ExploreResponseSerializer(serializers.ModelSerializer):
    post_id = serializers.CharField(source="id")
    thumbnail = serializers.URLField()
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    seed = serializers.IntegerField()

    class Meta:
        model = Post
        fields = ["post_id", "thumbnail", "like_count", "comment_count", "seed"]
