from django.core.cache import cache
from django.core.mail import send_mail
from redis import RedisError

from apps.core.exceptions.exception import (
    ExternalServiceException,
    InternalServerException,
    ValidationException,
)
from apps.core.utils.base62 import generate_6digits_safe, generate_token
from apps.users.redis_keys import EmailRedisKey


class EmailService:
    TTL = 180  # 3분
    TOKEN_TTL = 300  # 5분

    def send_email(self, email: str, purpose: str) -> None:
        code = generate_6digits_safe()
        cache_key = EmailRedisKey.code(purpose, email)
        try:
            cache.set(cache_key, code, self.TTL)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        try:
            send_mail(
                subject="[Danim] 이메일 인증 코드",
                message=f"인증 코드:{code}",
                from_email="",
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            cache.delete(cache_key)
            raise ExternalServiceException("이메일 발송에 실패했습니다.")

    def verify_code(self, email: str, code: str, purpose: str) -> str:
        cache_key = EmailRedisKey.code(purpose, email)

        try:
            cache_data = cache.get(cache_key)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        if not cache_data:
            raise ValidationException("인증 코드가 만료되었거나 존재하지 않습니다.")
        if cache_data != code:
            raise ValidationException("인증 코드가 틀렸습니다.")

        verify_token = generate_token()

        token_key = EmailRedisKey.token(purpose, verify_token)
        data = {"email": email}
        try:
            cache.set(token_key, data, self.TOKEN_TTL)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")
        cache.delete(cache_key)
        return verify_token
