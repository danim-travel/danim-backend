import math

from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.posts.models import PostSpot


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
    thumbnail = serializers.SerializerMethodField()
    place_name = serializers.CharField(source="location.place_name")
    x = serializers.CharField(source="location.x")
    y = serializers.CharField(source="location.y")
    distance = serializers.FloatField()

    def get_thumbnail(self, obj: PostSpot) -> str:
        """버킷이 비공개라 key 를 그대로 주면 403 이 난다. 서명된 URL 로 내려준다.

        게시글 상세·목록 등 다른 썸네일 응답과 같은 방식이다.
        """
        key = obj.post.thumbnail
        return s3_svc.create_download_presigned_url(key) if key else ""


class NearUserResponseSerializer(serializers.Serializer):
    top_near = NearPostSpotSerializer(many=True)
