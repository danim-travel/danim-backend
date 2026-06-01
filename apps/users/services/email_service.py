from django.core.mail import send_mail
from django_redis import cache
from redis import RedisError

from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import generate_6digits_safe, generate_token


class EmailService:
    TTL = 180  # 3분
    TOKEN_TTL = 300  # 5분

    def send_email(self, email: str, purpose: str) -> None:
        code = generate_6digits_safe()
        cache_key = f"email:code:{purpose}:{email}"
        try:
            cache.set(cache_key, code, self.TTL)
        except RedisError:
            raise ValidationException(
                "서버 오류, 다시 시도해주세요"
            )  # Todo: 공용 핸들러에서 500대 에러 핸들러 생성후 변경

        try:
            send_mail(
                subject="[Danim] 인증 코드",
                message=f"인증 코드:{code}",
                from_email="",
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception:
            cache.delete(cache_key)
            raise ValidationException(
                "이메일 발송에 실패했습니다."
            )  # Todo: 공용핸들러에서 500대 에러 핸들러 생성후 변경

    def verify_code(self, email: str, code: str, purpose: str) -> str:
        cache_key = f"email:code:{purpose}:{email}"

        try:
            cache_data = cache.get(cache_key)
        except RedisError:
            raise ValidationException("서버 오류, 다시 시도해주세요")

        if not cache_data:
            raise ValidationException("인증 코드가 만료되었거나 존재하지 않습니다.")
        if cache_data != code:
            raise ValidationException("인증 코드가 틀렸습니다.")

        verify_token = generate_token()

        token_key = f"email:token:{purpose}:{verify_token}"
        data = {"email": email}
        try:
            cache.set(token_key, data, self.TOKEN_TTL)
        except RedisError:
            raise ValidationException(
                "서버 오류, 다시 시도해주세요"
            )  # Todo: 공용핸들러에서 500대 에러 핸들러 생성후 변경
        cache.delete(cache_key)
        return verify_token
