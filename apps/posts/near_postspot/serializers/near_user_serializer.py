import math

from rest_framework import serializers


def _validate_coordinate(value):
    if not math.isfinite(value):
        raise serializers.ValidationError("유효하지 않은 좌표값 입니다.")


class NearUserQuerySerializer(serializers.Serializer):
    latitude = serializers.FloatField(
        min_value=-90, max_value=90, validators=[_validate_coordinate]
    )
    longitude = serializers.FloatField(
        min_value=-180, max_value=180, validators=[_validate_coordinate]
    )


class NearPostSpotSerializer(serializers.Serializer):
    post_id = serializers.CharField(source="post.id")
    thumbnail = serializers.CharField(source="post.thumbnail")
    place_name = serializers.CharField(source="location.place_name")
    x = serializers.CharField(source="location.x")
    y = serializers.CharField(source="location.y")
    distance = serializers.FloatField()


class NearUserResponseSerializer(serializers.Serializer):
    top_near = NearPostSpotSerializer(many=True)
