from datetime import date
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.users.validators import validate_nickname_format, validate_password_format


class UserSignUpSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=20, write_only=True)
    password_confirm = serializers.CharField(max_length=20, write_only=True)
    nickname = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=20)
    birth_day = serializers.DateField()
    profile_img = serializers.CharField(required=False)
    email_token = serializers.CharField()

    def validate_password(self, value: str) -> str:
        return validate_password_format(value)

    def validate_nickname(self, value: str) -> str:
        return validate_nickname_format(value)

    def validate_birth_day(self, value: date) -> date:
        """현재 날짜보다 높은 날짜 선택불가"""
        if value > date.today():
            raise ValidationError("생년월일은 오늘 이후 날짜일 수 없습니다.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """비밀번호 확인 검증"""
        if attrs["password"] != attrs["password_confirm"]:
            raise ValidationError("비밀번호가 일치하지 않습니다.")
        return attrs
