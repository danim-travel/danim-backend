from rest_framework import serializers


class NearUserQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()


class NearPostSpotSerializer(serializers.Serializer):
    post_id = serializers.CharField(source="post.id")
    thumbnail = serializers.CharField(source="post.thumbnail")
    place_name = serializers.CharField(source="location.place_name")
    x = serializers.CharField(source="location.x")
    y = serializers.CharField(source="location.y")


class NearUserResponseSerializer(serializers.Serializer):
    top_near = NearPostSpotSerializer(many=True)
