from rest_framework import serializers

from apps.posts.near_postspot.serializers.near_user_serializer import (
    NearPostSpotSerializer,
)


class NearPostQuerySerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=26)


class NearSpotsSerializer(serializers.Serializer):
    spot_id = serializers.CharField(max_length=26)
    top_near = NearPostSpotSerializer(many=True)


class NearPostResponseSerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=26)
    near_spots = NearSpotsSerializer(many=True)
