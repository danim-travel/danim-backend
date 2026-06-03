from datetime import datetime

from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.redis_keys import LoginRedisKey
from apps.core.exceptions.exception import UnauthorizedException, ValidationException


class LoginService:

    def login(self, email: str, password: str, old_refresh_token: str) -> tuple[str, str]:
        user = authenticate(email=email, password=password)

        if not user:
            raise UnauthorizedException("이메일 또는 비밀번호가 올바르지 않습니다.")

        if old_refresh_token:
            token = RefreshToken(old_refresh_token)  # type: ignore
            jti = token["jti"]

            cache_key = LoginRedisKey.blacklist(jti)

            if cache.get(cache_key):

                raise ValidationException("블랙리스트 토큰 입니다.")

            expire_at = token["exp"]

            now = int(datetime.now().timestamp())

            ttl = expire_at - now

            if ttl > 0:

                cache.set(cache_key, True, ttl)

        token = RefreshToken.for_user(user)

        access_token, refresh_token = str(token.access_token), str(token)

        return access_token, refresh_token
