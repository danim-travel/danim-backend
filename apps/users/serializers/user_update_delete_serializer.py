import re

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.core.storage.s3 import s3_svc
from apps.users.models import User


class UserUpdateRequestSerializer(serializers.Serializer):
    nickname = serializers.CharField(max_length=20, required=False)
    intro = serializers.CharField(max_length=100, required=False, allow_blank=True)
    key = serializers.CharField(max_length=255, required=False)

    # TODO: check_nickname 머지 후 validators.validate_nickname_format로 교체
    def validate_nickname(self, value: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValidationError("닉네임은 영문, 숫자, 언더바(_)만 사용가능합니다.")
        return value


class UserUpdateResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    intro = serializers.CharField(allow_null=True)
    profile_img = serializers.SerializerMethodField()

    # TODO: presigned 머지 후 obj.profile_img_url 프로퍼티로 교체
    def get_profile_img(self, obj: User) -> str | None:
        if not obj.profile_img:
            return None
        return s3_svc.create_img_url(obj.profile_img)
