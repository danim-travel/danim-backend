import re

from rest_framework.exceptions import ValidationError


def validate_nickname_format(value: str) -> str:
    """
    닉네임 영문,숫자,언더바(_)만 허용
    """
    if not re.match(r"^[a-zA-Z0-9_]+$", value):
        raise ValidationError("닉네임은 영문, 숫자, 언더바(_)만 사용 가능합니다.")
    return value


def validate_password_format(value: str) -> str:
    """
    비밀번호는 8자리 이상
    하나의 이상의 대문자 영어 포함
    하나 이상의 숫자 포함
    하나 이상의 특수문자 포함
    """
    if len(value) < 8:
        raise ValidationError("비밀번호는 8자리 이상이어야 합니다.")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("비밀번호는 하나 이상의 영문 대문자가 포함되어야 합니다.")
    if not re.search(r"\d", value):
        raise ValidationError("비밀번호는 하나 이상의 숫자가 포함되어야 합니다.")
    if not re.search(r"[!@#$%^&*()]", value):
        raise ValidationError(
            "비밀번호는 적어도 하나 이상의 특수문자(!@#$%^&*())가 포함되어야 합니다."
        )
    return value
