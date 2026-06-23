from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from redis import RedisError

from apps.core.exceptions.exception import (
    ExternalServiceException,
    InternalServerException,
    NotFoundException,
    TooManyRequestsException,
    ValidationException,
)
from apps.core.utils.base62 import generate_6digits_safe, generate_token
from apps.users.models.models import LoginType, User
from apps.users.redis_keys import EmailRedisKey


class EmailService:
    TTL = 180  # 3분
    TOKEN_TTL = 300  # 5분
    COOLDOWN = 60  # 발송 쿨다운
    MAX_VERIFY_ATTEMPTS = 5  # 인증코드 입력 횟수 한도

    def send_email(self, email: str, purpose: str) -> None:
        # 비밀번호 찾기는 가입된 이메일 로그인 유저에게만 발송한다.
        # (소셜 유저는 비밀번호가 없으므로 재설정 대상이 아님)
        if purpose == "find_password":
            self._assert_password_reset_eligible(email)

        cooldown_key = EmailRedisKey.cooldown(purpose, email)

        try:
            acquired = cache.add(cooldown_key, True, self.COOLDOWN)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        if not acquired:
            raise TooManyRequestsException("인증 메일은 잠시 후 다시 요청할 수 있습니다.")

        code = generate_6digits_safe()
        cache_key = EmailRedisKey.code(purpose, email)
        fail_key = EmailRedisKey.verify_fail(purpose, email)
        try:
            cache.set(cache_key, code, self.TTL)
            cache.delete(fail_key)  # 새 코드 발송 → 시도 횟수 리셋
        except RedisError:
            cache.delete(cooldown_key)
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        try:
            send_mail(
                subject="[Danim] 이메일 인증 코드",
                message=f"인증 코드:{code}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"이메일 발송 에러: {e}")
            cache.delete(cache_key)
            cache.delete(cooldown_key)
            raise ExternalServiceException("이메일 발송에 실패했습니다.")

    def verify_code(self, email: str, code: str, purpose: str) -> str:

        fail_key = EmailRedisKey.verify_fail(purpose, email)
        cache_key = EmailRedisKey.code(purpose, email)

        try:
            cache_data = cache.get(cache_key)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")

        if not cache_data:
            raise ValidationException("인증 코드가 만료되었거나 존재하지 않습니다.")
        if cache_data != code:
            try:
                if cache.add(fail_key, 1, self.TTL):
                    attempts = 1  # 첫 실패 → 1(+TTL)
                else:
                    attempts = cache.incr(fail_key)  # 이후 실패 → 증가
            except RedisError:
                raise InternalServerException("서버 오류, 다시 시도해주세요.")
            if attempts >= self.MAX_VERIFY_ATTEMPTS:
                cache.delete(cache_key)
                cache.delete(fail_key)
                raise TooManyRequestsException(
                    "인증 시도 횟수를 초과했습니다. 코드를 다시 요청해주세요."
                )
            raise ValidationException("인증 코드가 틀렸습니다.")

        verify_token = generate_token()

        token_key = EmailRedisKey.token(purpose, verify_token)
        data = {"email": email}
        try:
            cache.set(token_key, data, self.TOKEN_TTL)
        except RedisError:
            raise InternalServerException("서버 오류, 다시 시도해주세요.")
        cache.delete(cache_key)
        cache.delete(fail_key)
        return verify_token

    def _assert_password_reset_eligible(self, email: str) -> None:
        """비밀번호 재설정 대상(가입된 이메일 로그인 유저)인지 검증한다."""
        if not User.objects.filter(email=email, login_type=LoginType.EMAIL).exists():
            raise NotFoundException(
                "가입되지 않은 이메일이거나 비밀번호 재설정 대상이 아닙니다."
            )
