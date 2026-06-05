from unittest.mock import patch

from django.test import TestCase
from redis import RedisError

from apps.core.exceptions.exception import (
    ExternalServiceException,
    InternalServerException,
    NotFoundException,
    TooManyRequestsException,
    ValidationException,
)
from apps.users.models.models import LoginType, User
from apps.users.redis_keys import EmailRedisKey
from apps.users.services.email_service import EmailService


class EmailServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = EmailService()
        self.cache_patcher = patch("apps.users.services.email_service.cache")
        self.send_mail_patcher = patch("apps.users.services.email_service.send_mail")

        self.mock_cache = self.cache_patcher.start()
        self.mock_send_mail = self.send_mail_patcher.start()

        # 기본: 쿨다운 미적용(획득 성공). 차단 케이스에서만 False로 덮어씀
        self.mock_cache.add.return_value = True

        self.addCleanup(self.cache_patcher.stop)
        self.addCleanup(self.send_mail_patcher.stop)


class SendEmailTest(EmailServiceTest):

    def test_send_email_success(self) -> None:
        """이메일 발송 성공"""
        self.mock_cache.set.return_value = None
        self.mock_send_mail.return_value = None
        self.service.send_email("test@example.com", "signup")

    def test_send_email_redis_error(self) -> None:
        """Redis 저장 실패"""
        self.mock_cache.set.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.send_email("test@example.com", "signup")

    def test_send_email_mail_error(self) -> None:
        """이메일 발송 실패"""
        self.mock_cache.set.return_value = None
        self.mock_send_mail.side_effect = Exception
        with self.assertRaises(ExternalServiceException):
            self.service.send_email("test@example.com", "signup")

    def test_send_email_cooldown(self) -> None:
        """쿨다운 중 재발송 차단(429)"""
        self.mock_cache.add.return_value = False
        with self.assertRaises(TooManyRequestsException):
            self.service.send_email("test@example.com", "signup")

    def test_send_email_cooldown_redis_error(self) -> None:
        """쿨다운 키 확인 중 Redis 실패"""
        self.mock_cache.add.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.send_email("test@example.com", "signup")

    def test_send_email_rollback_cooldown_on_mail_failure(self) -> None:
        """발송 실패 시 쿨다운 키 롤백(delete)"""
        self.mock_cache.set.return_value = None
        self.mock_send_mail.side_effect = Exception
        cooldown_key = EmailRedisKey.cooldown("signup", "test@example.com")
        with self.assertRaises(ExternalServiceException):
            self.service.send_email("test@example.com", "signup")
        self.mock_cache.delete.assert_any_call(cooldown_key)

    def test_send_email_resets_fail_counter(self) -> None:
        """새 코드 발송 시 시도 횟수 카운터 리셋(delete)"""
        self.mock_cache.set.return_value = None
        self.mock_send_mail.return_value = None
        fail_key = EmailRedisKey.verify_fail("signup", "test@example.com")
        self.service.send_email("test@example.com", "signup")
        self.mock_cache.delete.assert_any_call(fail_key)


class FindPasswordSendEmailTest(EmailServiceTest):
    """find_password 발송 시 가입된 이메일 로그인 유저만 허용하는지 검증"""

    def _create_user(
        self, email: str, nickname: str, login_type: str = LoginType.EMAIL
    ) -> User:
        return User.objects.create_user(
            email=email,
            nickname=nickname,
            name="홍길동",
            birth_day="1990-01-01",
            login_type=login_type,
            is_active=True,
        )

    def test_find_password_eligible_user_sends(self) -> None:
        """가입된 이메일 유저 → 정상 발송"""
        self._create_user("user@example.com", "email_user")
        self.mock_cache.set.return_value = None
        self.mock_send_mail.return_value = None
        self.service.send_email("user@example.com", "find_password")
        self.mock_send_mail.assert_called_once()

    def test_find_password_unknown_email_raises(self) -> None:
        """가입되지 않은 이메일 → 404, 발송/쿨다운 없음"""
        with self.assertRaises(NotFoundException):
            self.service.send_email("ghost@example.com", "find_password")
        self.mock_cache.add.assert_not_called()
        self.mock_send_mail.assert_not_called()

    def test_find_password_social_user_raises(self) -> None:
        """소셜 로그인 유저 → 재설정 대상 아님(404)"""
        self._create_user("kakao@example.com", "kakao_user", login_type=LoginType.KAKAO)
        with self.assertRaises(NotFoundException):
            self.service.send_email("kakao@example.com", "find_password")
        self.mock_send_mail.assert_not_called()


class VerifyCodeTest(EmailServiceTest):

    def test_verify_code_success(self) -> None:
        """코드 검증 성공"""
        self.mock_cache.get.return_value = "123456"
        self.mock_cache.set.return_value = None
        token = self.service.verify_code("test@example.com", "123456", "signup")
        self.assertIsNotNone(token)

    def test_verify_code_expired(self) -> None:
        """코드 만료"""
        self.mock_cache.get.return_value = None
        with self.assertRaises(ValidationException):
            self.service.verify_code("test@example.com", "123456", "signup")

    def test_verify_code_mismatch(self) -> None:
        """코드 불일치"""
        self.mock_cache.get.return_value = "654321"
        with self.assertRaises(ValidationException):
            self.service.verify_code("test@example.com", "123456", "signup")

    def test_verify_code_redis_get_error(self) -> None:
        """Redis 조회 실패"""
        self.mock_cache.get.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.verify_code("test@example.com", "123456", "signup")

    def test_verify_code_token_save_error(self) -> None:
        """토큰 저장 실패"""
        self.mock_cache.get.return_value = "123456"
        self.mock_cache.set.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.verify_code("test@example.com", "123456", "signup")

    def test_verify_code_wrong_under_limit(self) -> None:
        """한도 미만 오답 → ValidationException"""
        self.mock_cache.get.return_value = "654321"
        self.mock_cache.add.return_value = False
        self.mock_cache.incr.return_value = 3
        with self.assertRaises(ValidationException):
            self.service.verify_code("test@example.com", "123456", "signup")

    def test_verify_code_brute_force_limit(self) -> None:
        """틀린 횟수 한도 초과 → 코드 무효화 + 429"""
        self.mock_cache.get.return_value = "654321"
        self.mock_cache.add.return_value = False
        self.mock_cache.incr.return_value = self.service.MAX_VERIFY_ATTEMPTS
        cache_key = EmailRedisKey.code("signup", "test@example.com")
        with self.assertRaises(TooManyRequestsException):
            self.service.verify_code("test@example.com", "123456", "signup")
        self.mock_cache.delete.assert_any_call(cache_key)  # 코드 무효화 확인

    def test_verify_code_fail_count_redis_error(self) -> None:
        """틀린 횟수 카운트 중 Redis 실패 → 500"""
        self.mock_cache.get.return_value = "654321"
        self.mock_cache.add.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.verify_code("test@example.com", "123456", "signup")
