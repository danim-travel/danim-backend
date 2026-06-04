from datetime import date
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from redis import RedisError

from apps.core.exceptions.exception import (
    ConflictException,
    InternalServerException,
    NotFoundException,
)
from apps.users.models import User
from apps.users.services.signup_service import SignUpService


class SignUpServiceTest(TestCase):
    def setUp(self) -> None:
        self.service = SignUpService()
        self.cache_patcher = patch("apps.users.services.signup_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)

    def _validated_data(self, **kwargs):
        data = {
            "email_token": "abc123",
            "password": "Password@1",
            "password_confirm": "Password@1",
            "nickname": "testnickname",
            "name": "testname",
            "birth_day": date(1999, 1, 1),
        }
        data.update(kwargs)
        return data

    def test_create_user_success(self) -> None:
        """회원가입 성공"""
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        user = self.service.create_user(self._validated_data())
        self.assertIsInstance(user, User)
        self.assertEqual(user.email, "test@example.com")

    def test_create_user_invalid_token(self) -> None:
        """유효하지 않은 이메일 토큰"""
        self.mock_cache.get.return_value = None
        with self.assertRaises(NotFoundException):
            self.service.create_user(self._validated_data())

    def test_create_user_duplicate_email(self) -> None:
        """이메일 중복"""
        User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="othernickname",
            name="testname",
            birth_day=date(1999, 1, 1),
        )
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        with self.assertRaises(ConflictException):
            self.service.create_user(self._validated_data())

    def test_create_user_duplicate_nickname(self) -> None:
        """닉네임 중복"""
        User.objects.create_user(
            email="other@example.com",
            password="Password@1",
            nickname="testnickname",
            name="testname",
            birth_day=date(1999, 1, 1),
        )
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        with self.assertRaises(ConflictException):
            self.service.create_user(self._validated_data())

    @patch("apps.users.services.signup_service.User.objects.create_user")
    def test_create_user_race_integrity_error(self, mock_create_user) -> None:
        """동시 가입 race → INSERT가 unique 제약에 걸리면 ConflictException(409)"""
        mock_create_user.side_effect = IntegrityError
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        with self.assertRaises(ConflictException):
            self.service.create_user(self._validated_data())

    def test_create_user_invalid_email_data(self) -> None:
        """Redis 데이터에 email 키 없음"""
        self.mock_cache.get.return_value = {}
        with self.assertRaises(NotFoundException):
            self.service.create_user(self._validated_data())

    def test_create_user_empty_email(self) -> None:
        """Redis 데이터에 email 값이 빈 문자열"""
        self.mock_cache.get.return_value = {"email": ""}
        with self.assertRaises(NotFoundException):
            self.service.create_user(self._validated_data())

    def test_create_user_redis_error_on_get(self) -> None:
        """cache.get 호출 시 RedisError 발생"""
        self.mock_cache.get.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.create_user(self._validated_data())

    def test_create_user_redis_error_on_delete(self) -> None:
        """cache.delete 호출 시 RedisError 발생"""
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        self.mock_cache.delete.side_effect = RedisError
        with self.assertRaises(InternalServerException):
            self.service.create_user(self._validated_data())
