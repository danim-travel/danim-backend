import re
from datetime import date
from typing import Any

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UserSignUpSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=20, write_only=True)
    password_confirm = serializers.CharField(max_length=20, write_only=True)
    nickname = serializers.CharField(max_length=20)
    name = serializers.CharField(max_length=20)
    birth_day = serializers.DateField()
    profile_img = serializers.CharField(required=False)
    email_token = serializers.CharField()

    def validate_password(self, value: str) -> str:
        """
        비밀번호는 8자리 이상
        하나의 이상의 대문자 영어 포함
        하나 이상의 숫자 포함
        하나 이상의 특수문자 포함
        """
        if len(value) < 8:
            raise ValidationError("비밀번호는 8자리 이상이어야 합니다.")
        if not re.search(r"[A-Z]", value):
            raise ValidationError(
                "비밀번호는 하나 이상의 영문 대문자가 포함되어야 합니다."
            )
        if not re.search(r"\d", value):
            raise ValidationError("비밀번호는 하나 이상의 숫자가 포함되어야 합니다.")
        if not re.search(r"[!@#$%^&*()]", value):
            raise ValidationError(
                "비밀번호는 적어도 하나 이상의 특수문자(!@#$%^&*())가 포함되어야 합니다."
            )
        return value

    def validate_nickname(self, value: str) -> str:
        """
        닉네임 영문,숫자,언더바(_)만 허용
        """
        if not re.match(r"^[a-zA-Z0-9_]+$", value):
            raise ValidationError("닉네임은 영문, 숫자, 언더바(_)만 사용 가능합니다.")
        return value

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
