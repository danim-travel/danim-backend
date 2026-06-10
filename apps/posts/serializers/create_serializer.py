from rest_framework import serializers


class PostSpotImageCreateSerializer(serializers.Serializer):
    """게시글 핀 이미지 생성 Request Body 검증 serializer"""

    original_img = serializers.CharField()
    key = serializers.CharField()


class LocationCreateSerializer(serializers.Serializer):
    """게시글 핀 위치 생성 Request Body 검증 serializer"""

    place_name = serializers.CharField(max_length=255)
    address_name = serializers.CharField(max_length=255)
    road_address_name = serializers.CharField(max_length=255)
    x = serializers.CharField()
    y = serializers.CharField()


class PostSpotCreateSerializer(serializers.Serializer):
    """게시글 핀 생성 Request Body 검증 serializer"""

    order = serializers.IntegerField()
    content = serializers.CharField(required=False, allow_blank=True, default="")
    location = LocationCreateSerializer()
    images = PostSpotImageCreateSerializer(many=True, required=False, default=list)


class PostCreateSerializer(serializers.Serializer):
    """게시글 생성 Request Body 검증 serializer"""

    title = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    thumbnail = serializers.CharField(required=False, allow_blank=True, default="")
    spots = PostSpotCreateSerializer(many=True, required=False, default=list)
