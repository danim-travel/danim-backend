from rest_framework import serializers


class PostSpotImageUpdateSerializer(serializers.Serializer):
    original_img = serializers.CharField()
    key = serializers.CharField()


class LocationUpdateSerializer(serializers.Serializer):
    place_name = serializers.CharField(max_length=255)
    address_name = serializers.CharField(max_length=255)
    road_address_name = serializers.CharField(max_length=255)
    x = serializers.CharField()
    y = serializers.CharField()


class PostSpotUpdateSerializer(serializers.Serializer):
    id = serializers.CharField(required=False)
    order = serializers.IntegerField()
    content = serializers.CharField(required=False, allow_blank=True, default="")
    location = LocationUpdateSerializer()
    images = PostSpotImageUpdateSerializer(many=True, required=False, default=list)


class PostUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    thumbnail = serializers.CharField(required=False, allow_blank=True)
    spots = PostSpotUpdateSerializer(many=True, required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                {"title": ["최소 하나의 필드를 수정해야 합니다."]}
            )
        return attrs
