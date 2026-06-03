from datetime import datetime

from django.contrib.auth import authenticate
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import UnauthorizedException, ValidationException
from apps.users.redis_keys import LoginRedisKey


def _blacklist_refresh_token(refresh_token: str) -> None:
    """refresh_token을 만료 시점까지 블랙리스트에 등록. 이미 만료/손상된 토큰은 무시한다."""
    try:
        token = RefreshToken(refresh_token)  # type: ignore[arg-type]
    except TokenError:
        return

    ttl = int(token["exp"]) - int(datetime.now().timestamp())
    if ttl > 0:
        cache.set(LoginRedisKey.blacklist(token["jti"]), True, ttl)


class LoginService:

    def login(self, email: str, password: str, old_refresh_token: str) -> tuple[str, str]:
        user = authenticate(email=email, password=password)

        if not user:
            raise UnauthorizedException("이메일 또는 비밀번호가 올바르지 않습니다.")

        if old_refresh_token:
            _blacklist_refresh_token(old_refresh_token)

        token = RefreshToken.for_user(user)
        access_token, refresh_token = str(token.access_token), str(token)

        return access_token, refresh_token


class LogoutService:

    def logout(self, refresh_token: str) -> None:
        if not refresh_token:
            raise ValidationException("로그아웃을 위한 토큰이 없습니다.")

        _blacklist_refresh_token(refresh_token)
