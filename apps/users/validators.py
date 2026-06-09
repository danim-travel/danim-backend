import re

from rest_framework.exceptions import ValidationError


def validate_nickname_format(value: str) -> str:
    """
    닉네임 영문,숫자,언더바(_)만 허용
    """
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise ValidationError("닉네임은 영문, 숫자, 언더바(_)만 사용 가능합니다.")
    return value
