from datetime import date
from unittest.mock import patch

from django.urls import reverse
from redis import RedisError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


class BaseViewTest(APITestCase):
    user: User

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            birth_day=date(1970, 1, 1),
        )

    def setUp(self) -> None:
        super().setUp()
        self.cache_patcher = patch("apps.users.services.email_service.cache")
        self.send_mail_patcher = patch("apps.users.services.email_service.send_mail")

        self.mock_cache = self.cache_patcher.start()
        self.mock_send_mail = self.send_mail_patcher.start()

        self.addCleanup(self.cache_patcher.stop)
        self.addCleanup(self.send_mail_patcher.stop)


class EmailSendViewTest(BaseViewTest):

    def test_send_email_success(self) -> None:
        self.mock_cache.set.return_value = None
        self.mock_send_mail.return_value = None
        response = self.client.post(
            reverse("users:send_email"),
            {"email": "test@example.com", "purpose": "signup"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_send_email_invalid_email(self) -> None:
        response = self.client.post(
            reverse("users:send_email"), {"email": "", "purpose": "signup"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_email_mail_error(self) -> None:
        self.mock_cache.set.return_value = None
        self.mock_send_mail.side_effect = Exception
        response = self.client.post(
            reverse("users:send_email"),
            {"email": "test@example.com", "purpose": "signup"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_send_email_redis_error(self) -> None:
        self.mock_cache.set.side_effect = RedisError
        response = self.client.post(
            reverse("users:send_email"),
            {"email": "test@example.com", "purpose": "signup"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EmailVerifyViewTest(BaseViewTest):

    def test_verify_code_success(self) -> None:
        """이메일 인증 test code"""
        self.mock_cache.get.return_value = "123456"
        self.mock_cache.set.return_value = None
        response = self.client.post(
            reverse("users:verify_email"),
            {
                "email": "test@example.com",
                "code": "123456",
                "purpose": "signup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_verify_code_expired(self) -> None:
        """코드 만료 test code"""
        self.mock_cache.get.return_value = None
        response = self.client.post(
            reverse("users:verify_email"),
            {
                "email": "test@example.com",
                "code": "123456",
                "purpose": "signup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_code_mismatch(self) -> None:
        """코드 불일치 test code"""
        self.mock_cache.get.return_value = "123456"
        self.mock_cache.set.return_value = None
        response = self.client.post(
            reverse("users:verify_email"),
            {
                "email": "test@example.com",
                "code": "123455",
                "purpose": "signup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_code_redis_get_error(self) -> None:
        """Redis 조회 실패 test code"""
        self.mock_cache.get.side_effect = RedisError
        response = self.client.post(
            reverse("users:verify_email"),
            {
                "email": "test@example.com",
                "code": "123455",
                "purpose": "signup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_code_token_save_error(self) -> None:
        """토큰 저장 실패 test code"""
        self.mock_cache.get.return_value = "123456"
        self.mock_cache.set.side_effect = RedisError
        response = self.client.post(
            reverse("users:verify_email"),
            {
                "email": "test@example.com",
                "code": "123455",
                "purpose": "signup",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
