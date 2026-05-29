from pathlib import Path
from typing import Any

from rest_framework import serializers

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3.constants import ALLOWED_EXTENSIONS


class PresignedUrlRequestSerializer(serializers.Serializer[Any]):
    """presigned_url용 원본 파일명을 받는 시리얼라이저"""

    original_img = serializers.CharField(max_length=100)

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        original_img = attrs["original_img"]

        # 확장자 소문자로 통일
        path = Path(original_img)
        extension = path.suffix.lower()

        # 허용된 확장자만 통과
        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationException(detail="지원하지 않는 파일 형식입니다.")

        # 확장자, content_type를 attrs에 저장
        attrs["extension"] = extension
        attrs["content_type"] = ALLOWED_EXTENSIONS[extension]

        return attrs


class PresignedUrlResponseSerializer(serializers.Serializer[Any]):
    """
    presigned url 응답 시리얼라이저
    """

    presigned_url = serializers.CharField()
    img_url = serializers.CharField()
    key = serializers.CharField(max_length=255)
