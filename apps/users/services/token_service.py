from django.core.cache import caches
from redis import RedisError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import (
    ForbiddenException,
    InternalServerException,
    ValidationException,
)
from apps.users.redis_keys import LoginRedisKey

# 토큰 블랙리스트는 인증 상태 — fail-closed 별칭. default 별칭은
# IGNORE_EXCEPTIONS=True라 장애 시 None을 돌려줘 아래 RedisError 캐치에
# 도달하지 못하고, 로그아웃된 토큰이 재발급되는 fail-open이 된다.
# (이름을 cache로 유지해 기존 테스트의 patch 대상 호환)
cache = caches["auth"]


class TokenService:

    def refresh_access_token(self, refresh_token: str) -> str:
        if not refresh_token:
            raise ValidationException("재발급을 위한 토큰이 없습니다.")

        try:
            token = RefreshToken(refresh_token)  # type: ignore[arg-type]
        except TokenError:
            raise ForbiddenException("로그인 세션이 만료되었습니다.")

        try:
            is_blacklisted = cache.get(LoginRedisKey.blacklist(token["jti"]))
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        if is_blacklisted:  # 로그아웃/재로그인으로 블랙리스트된 토큰은 재발급 차단
            raise ForbiddenException("로그아웃된 토큰입니다.")

        return str(token.access_token)
