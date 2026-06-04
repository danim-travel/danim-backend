from typing import Any

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q
from redis import RedisError

from apps.core.exceptions.exception import (
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from apps.users.models import User
from apps.users.redis_keys import EmailRedisKey


class SignUpService:

    def create_user(self, validated_data: dict[str, Any]) -> User:

        email_token = validated_data.pop("email_token")
        password = validated_data.pop("password")
        validated_data.pop("password_confirm")
        nickname = validated_data.pop("nickname")

        email_key = EmailRedisKey.token("signup", email_token)
        try:
            email_data = cache.get(email_key)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

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

            # 신규 email/nickname은 select_for_update가 못 잠가서, 동시 가입 시
            # 검사를 둘 다 통과하고 INSERT에서 unique 제약에 걸릴 수 있음 → 409로 변환
            try:
                user = User.objects.create_user(
                    email=email,
                    nickname=nickname,
                    password=password,
                    is_active=True,
                    is_email_verified=True,
                    **validated_data,
                )
            except IntegrityError:
                raise ConflictException("이미 존재하는 이메일 또는 닉네임입니다.")

            try:
                cache.delete(email_key)
            except RedisError:
                raise InternalServerException("서버 오류, 다시 시도해주세요.") # TODO:409로 에러 변경
            return user
