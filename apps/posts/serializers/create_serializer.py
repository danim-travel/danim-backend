from rest_framework import serializers

from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import validate_attach_key


class PostSpotImageCreateSerializer(serializers.Serializer):
    """게시글 핀 이미지 생성 Request Body 검증 serializer"""

    original_img = serializers.CharField()
    key = serializers.CharField(max_length=255)
    width = serializers.IntegerField(min_value=1)
    height = serializers.IntegerField(min_value=1)

    def validate_key(self, value: str) -> str:
        # post 카테고리로 발급된 key만 허용 — DM 등 다른 문맥의 key를
        # 게시글에 심어 공개 재배포하는 교차 카테고리 세탁 차단
        return validate_attach_key(value, CategoryEnum.POST)


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
    thumbnail_width = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, default=None
    )
    thumbnail_height = serializers.IntegerField(
        required=False, allow_null=True, min_value=1, default=None
    )
    spots = PostSpotCreateSerializer(many=True, required=False, default=list)

    def validate_thumbnail(self, value: str) -> str:
        if not value:  # 빈 값 = 썸네일 없음 (기존 계약 유지)
            return value
        return validate_attach_key(value, CategoryEnum.POST)

    def validate(self, attrs):
        if attrs.get("thumbnail") and (
            attrs.get("thumbnail_width") is None or attrs.get("thumbnail_height") is None
        ):
            raise serializers.ValidationError(
                {
                    "thumbnail_width": [
                        "썸네일이 있으면 width/height도 함께 보내야 합니다."
                    ]
                }
            )
        return attrs
