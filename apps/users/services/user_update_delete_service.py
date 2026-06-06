from typing import Any

from django.db import IntegrityError

from apps.core.exceptions.exception import ConflictException
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
