from typing import Any

from django.contrib.auth.handlers.modwsgi import check_password
from django.db import IntegrityError

from apps.core.exceptions.exception import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)
from apps.users.models import User


class UserUpdateService:

    def user_update(self, user: User, data: dict[str, Any]) -> User:
        if data.get("nickname"):
            if (
                User.objects.exclude(pk=user.pk)
                .filter(nickname=data["nickname"])
                .exists()
            ):
                raise ConflictException("중복된 닉네임 입니다.")

        if data.get("nickname"):
            user.nickname = data["nickname"]

        if "intro" in data:
            user.intro = data["intro"]

        if data.get("key") is not None:
            user.profile_img = data["key"]
        try:
            user.save()
        except IntegrityError:
            raise ConflictException("중복된 닉네임 입니다.")
        return user


class UserDeleteService:
    def user_delete(self, user: User, password: str) -> None:
        if not password:
            raise ValidationException("비밀번호를 입력해 주세요.")
        if not user.check_password(password):
            raise UnauthorizedException("비밀번호가 틀립니다.")

        user.delete()
