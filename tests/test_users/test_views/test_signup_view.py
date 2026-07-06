from unittest.mock import patch

from django.urls import reverse
from rest_framework import status

from tests.test_core.bases.user_base import UserViewBase


class BaseViewTest(UserViewBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setUp(self) -> None:
        super().setUp()
        self.cache_patcher = patch("apps.users.services.signup_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)


class UserSignUpViewTest(BaseViewTest):

    def test_signup_success(self) -> None:
        """회원가입 성공"""
        self.mock_cache.get.return_value = {"email": "test1@example.com"}
        response = self.client.post(
            reverse("users:signup"),
            {
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "newuser",
                "name": "testname",
                "birth_day": "1999-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_signup_email_duplication(self) -> None:
        """이메일 중복"""
        self.mock_cache.get.return_value = {"email": "test@example.com"}
        response = self.client.post(
            reverse("users:signup"),
            {
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "owner_nick",
                "name": "testname",
                "birth_day": "1999-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_signup_nickname_duplication(self) -> None:
        """닉네임 중복"""
        self.mock_cache.get.return_value = {"email": "test1@example.com"}
        response = self.client.post(
            reverse("users:signup"),
            {
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "owner_nick",
                "name": "testname",
                "birth_day": "1999-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_signup_invalid_token(self) -> None:
        """유효하지 않은 토큰"""
        self.mock_cache.get.return_value = None
        response = self.client.post(
            reverse("users:signup"),
            {
                "email_token": "abc123",
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "test",
                "name": "testname",
                "birth_day": "1999-01-01",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
