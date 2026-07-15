from django.core.cache import caches
from redis import RedisError

from apps.core.exceptions.exception import InternalServerException, UnauthorizedException
from apps.users.models import LoginType, User
from apps.users.redis_keys import EmailRedisKey

# 소셜 state·인증/재설정 토큰은 인증 상태 — fail-closed 별칭 사용
# (이름을 cache로 유지해 기존 테스트의 patch 대상 호환)
cache = caches["auth"]


class ResetPasswordService:
    PURPOSE = "find_password"

    def reset_password(self, email_token: str, new_password: str) -> None:
        cache_key = EmailRedisKey.token(self.PURPOSE, email_token)

        try:
            data = cache.get(cache_key)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요")

        if not data:
            raise UnauthorizedException("유효하지 않은 토큰입니다.")

        email = data.get("email")
        user = User.objects.filter(email=email, login_type=LoginType.EMAIL).first()
        if not user:
            raise UnauthorizedException("유효하지 않은 토큰입니다.")

        user.set_password(new_password)
        user.save(update_fields=["password"])
        cache.delete(cache_key)
