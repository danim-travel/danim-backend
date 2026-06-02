from typing import Any

from django.core.cache import cache
from django.db import transaction
from django.db.models import Q

from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.users.models import User


class SignUpService:

    def create_user(self, validated_data: dict[str, Any]) -> User:

        email_token = validated_data.pop("email_token")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")
        nickname = validated_data.pop("nickname")

        email_key = f"email:token:signup:{email_token}"
        email_data = cache.get(email_key)

        if not email_data:
            raise NotFoundException("유효하지 않은 이메일입니다.")

        email = email_data.get("email")

        if not email:
            raise NotFoundException("유효하지 않은 이메일입니다.")

        with transaction.atomic():
            existing_accounts = User.objects.select_for_update().filter(
                Q(email=email) | Q(nickname=nickname)
            )
            for user in existing_accounts:
                if user.email == email:
                    raise ConflictException("이미 존재하는 이메일 입니다.")
                if user.nickname == nickname:
                    raise ConflictException("이미 존재하는 닉네임 입니다.")

            user = User.objects.create_user(
                email=email,
                nickname=nickname,
                password=password,
                is_active=True,
                is_email_verified=True,
                **validated_data,
            )

            cache.delete(email_key)
            return user
