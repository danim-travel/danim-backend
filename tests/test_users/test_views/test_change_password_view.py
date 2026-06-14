from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import LoginType, User


class ChangePasswordViewTest(APITestCase):
    user: User
    user2: User

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.EMAIL,
        )
        cls.user2 = User.objects.create_user(
            email="social@example.com",
            password="Password@1",
            nickname="social_nick",
            name="social",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.KAKAO,
        )

    def test_change_password_view(self) -> None:
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("users:change_password"),
            {
                "password": "Password@1",
                "new_password": "Password@2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_password_no_auth(self) -> None:
        """인증 없이 요청 → 401"""
        response = self.client.post(
            reverse("users:change_password"),
            {
                "password": "Password@1",
                "new_password": "Password@2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_social_user(self) -> None:
        """소셜 로그인 유저 → 403"""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(
            reverse("users:change_password"),
            {
                "password": "Password@1",
                "new_password": "Password@2",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
