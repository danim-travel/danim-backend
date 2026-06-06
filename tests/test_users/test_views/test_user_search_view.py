from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.users.models import User


class BaseViewTest(APITestCase):
    user1: User
    user2: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user1 = User.objects.create_user(
            email="test1@example.com",
            password="Password@1",
            nickname="test_nick1",
            name="tim",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

        cls.user2 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test_nick2",
            name="sam",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )


class UserSearchViewTest(BaseViewTest):

    def test_user_search_view(self) -> None:
        """유저 검색 성공"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("users:user_search"), {"search": "tim"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["user_id"], self.user1.id)

    def test_user_search_view_without_search(self) -> None:
        """빈값을 준 유저 검색"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("users:user_search"), {"search": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
