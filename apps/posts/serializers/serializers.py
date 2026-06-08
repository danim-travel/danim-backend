from rest_framework import serializers


class ImageSerializer(serializers.Serializer):
    key = serializers.CharField()
    original_img = serializers.CharField()


class LocationSerializer(serializers.Serializer):
    address_name = serializers.CharField(max_length=255)
    road_address_name = serializers.CharField(max_length=255)
    place_name = serializers.CharField(max_length=255)
    x = serializers.DecimalField(max_digits=17, decimal_places=14)
    y = serializers.DecimalField(max_digits=17, decimal_places=14)


class SpotSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    content = serializers.CharField()
    location = LocationSerializer()
    images = ImageSerializer(many=True)


class PostCreateRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100)
    description = serializers.CharField()
    thumbnail = serializers.CharField()
    spots = SpotSerializer(many=True)
