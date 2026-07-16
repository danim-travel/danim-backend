from datetime import datetime

from django.contrib.auth import authenticate
from django.core.cache import caches
from redis import RedisError
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import (
    InternalServerException,
    UnauthorizedException,
    ValidationException,
)
from apps.users.redis_keys import LoginRedisKey

# 토큰 블랙리스트는 인증 상태 — fail-closed 별칭 사용
# (이름을 cache로 유지해 기존 테스트의 patch 대상 호환)
cache = caches["auth"]


def _blacklist_refresh_token(refresh_token: str) -> None:
    """refresh_token을 만료 시점까지 블랙리스트에 등록. 이미 만료/손상된 토큰은 무시한다.

    블랙리스트 등록 실패는 삼키지 않는다(fail-closed) — 실패를 삼키고 200을
    돌려주면 사용자는 로그아웃됐다고 믿지만 토큰은 만료까지 살아 있다.
    """
    try:
        token = RefreshToken(refresh_token)  # type: ignore[arg-type]
    except TokenError:
        return

    ttl = int(token["exp"]) - int(datetime.now().timestamp())
    if ttl > 0:
        try:
            cache.set(LoginRedisKey.blacklist(token["jti"]), True, ttl)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")


class LoginService:

    def login(self, email: str, password: str, old_refresh_token: str) -> tuple[str, str]:
        user = authenticate(email=email, password=password)

        if not user:
            raise UnauthorizedException("이메일 또는 비밀번호가 올바르지 않습니다.")

        if old_refresh_token:
            _blacklist_refresh_token(old_refresh_token)

        token = RefreshToken.for_user(user)
        # 프론트가 토큰 디코딩만으로 소셜 로그인 여부를 판별할 수 있도록 담는다.
        # (access_token 생성 전에 set하면 access_token에도 복사되고, 재발급 시에도 유지됨)
        token["login_type"] = user.login_type
        access_token, refresh_token = str(token.access_token), str(token)

        return access_token, refresh_token


class LogoutService:

    def logout(self, refresh_token: str) -> None:
        if not refresh_token:
            raise ValidationException("로그아웃을 위한 토큰이 없습니다.")

        _blacklist_refresh_token(refresh_token)
