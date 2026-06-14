from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User


class ChangePasswordViewTest(APITestCase):
    user: User

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
            login_type="email",
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
