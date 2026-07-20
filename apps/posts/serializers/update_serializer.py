from rest_framework import serializers

from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import validate_attach_key


class PostSpotImageUpdateSerializer(serializers.Serializer):
    original_img = serializers.CharField()
    key = serializers.CharField(max_length=255)
    width = serializers.IntegerField(min_value=1)
    height = serializers.IntegerField(min_value=1)

    def validate_key(self, value: str) -> str:
        # post 카테고리로 발급된 key만 허용 (create와 동일 계약)
        return validate_attach_key(value, CategoryEnum.POST)


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
    thumbnail_width = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    thumbnail_height = serializers.IntegerField(
        required=False, allow_null=True, min_value=1
    )
    spots = PostSpotUpdateSerializer(many=True, required=False)

    def validate_thumbnail(self, value: str) -> str:
        if not value:  # 빈 값 = 썸네일 제거/없음 (기존 계약 유지)
            return value
        return validate_attach_key(value, CategoryEnum.POST)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                {"title": ["최소 하나의 필드를 수정해야 합니다."]}
            )
        # 썸네일을 새로 바꾸는 거면 그 이미지의 width/height도 같이 와야 함
        # (예전 썸네일의 크기를 새 썸네일에 그대로 쓸 수 없으므로)
        if attrs.get("thumbnail") and (
            attrs.get("thumbnail_width") is None or attrs.get("thumbnail_height") is None
        ):
            raise serializers.ValidationError(
                {
                    "thumbnail_width": [
                        "썸네일을 변경하려면 width/height도 함께 보내야 합니다."
                    ]
                }
            )
        return attrs
