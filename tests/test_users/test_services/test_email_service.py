from unittest.mock import patch

from django.test import TestCase
from redis import RedisError

from apps.core.exceptions.exception import (
    ExternalServiceException,
    InternalServerException,
    ValidationException,
)
from apps.users.services.email_service import EmailService


class EmailServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = EmailService()
        self.cache_patcher = patch("apps.users.services.email_service.cache")
        self.send_mail_patcher = patch("apps.users.services.email_service.send_mail")

        self.mock_cache = self.cache_patcher.start()
        self.mock_send_mail = self.send_mail_patcher.start()

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
