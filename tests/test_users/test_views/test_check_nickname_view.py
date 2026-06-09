from datetime import date

from django.urls import reverse
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


class CheckNicknameViewTest(BaseViewTest):

    def test_check_success(self) -> None:
        """사용 가능한 닉네임"""
        response = self.client.post(
            reverse("users:check_nickname"), {"nickname": "test_nickname"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_check_duplicate_nickname(self) -> None:
        """중복된 닉네임"""
        response = self.client.post(reverse("users:check_nickname"), {"nickname": "test"})
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_check_nickname_invalid(self) -> None:
        """유효하지 않은 닉네임"""
        response = self.client.post(
            reverse("users:check_nickname"), {"nickname": "테스트_닉네임"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
