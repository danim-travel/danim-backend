from django.urls import reverse
from rest_framework import status

from tests.test_core.bases.user_base import UserViewBase


class BaseViewTest(UserViewBase):

    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()


class UserSearchViewTest(BaseViewTest):

    def test_user_search_view(self) -> None:
        """유저 검색 성공"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("users:user_search"), {"search": "owner"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["user_id"], self.user1.id)

    def test_user_search_view_without_search(self) -> None:
        """빈값을 준 유저 검색"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse("users:user_search"), {"search": ""})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
