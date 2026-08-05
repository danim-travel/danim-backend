from rest_framework import serializers


class ExploreQuerySerializer(serializers.Serializer):
    search = serializers.CharField(required=False, default=None, allow_blank=True)
    region = serializers.CharField(required=False, default=None, allow_blank=True)
    cursor = serializers.CharField(required=False, default=None, allow_blank=True)
    page_size = serializers.IntegerField(required=False, default=10)
    seed = serializers.IntegerField(required=False, default=None)

    def validate_page_size(self, value):
        if value != 10:
            return 10
        return value


class ExploreFeedsSerializer(serializers.Serializer):
    post_id = serializers.CharField(source="id")
    thumbnail = serializers.URLField()
    thumbnail_width = serializers.IntegerField(allow_null=True)
    thumbnail_height = serializers.IntegerField(allow_null=True)
    like_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()


class ExploreResponseSerializer(serializers.Serializer):
    next = serializers.URLField(allow_null=True)
    seed = serializers.IntegerField()
    results = ExploreFeedsSerializer(many=True)
