from django.urls import reverse
from rest_framework import status

from tests.test_core.bases.user_base import UserViewBase


class ChangePasswordViewTest(UserViewBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_change_password_view(self) -> None:
        self.client.force_authenticate(user=self.user1)
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
