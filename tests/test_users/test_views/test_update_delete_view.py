from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.storage.s3 import s3_svc
from apps.users.models import User


class BaseTestCase(APITestCase):
    user1: User
    user2: User
    user3: User

    @classmethod
    def setUpTestData(cls):
        # 모든 데이터를 가지고 있는 유저
        cls.user1 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            intro="test_intro",
            birth_day=date(1970, 1, 1),
            profile_img="test_key",
        )

        # 프로필 이미지가 None인 유저
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
        )

        # 소개글이 None인 유저
        cls.user3 = User.objects.create_user(
            email="test3@example.com",
            password="Password@1",
            nickname="test3",
            name="name",
            profile_img="test_key",
            birth_day=date(1999, 1, 1),
        )


class UpdateViewTest(BaseTestCase):

    def test_update_success(self) -> None:
        """user 업데이트 성공"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            reverse("users:user_update_delete"),
            data={
                "nickname": "update_nickname",
                "intro": "update_intro",
                "key": "update_key",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], "update_nickname")
        self.assertEqual(response.data["intro"], "update_intro")
        self.assertEqual(
            response.data["profile_img"], s3_svc.create_img_url("update_key")
        )

    def test_user_not_unauthorized(self) -> None:
        """비 로그인 유저가 업데이트 보낼떄 (401)"""
        response = self.client.patch(
            reverse("users:user_update_delete"),
            data={
                "nickname": "update_nickname",
                "intro": "update_intro",
                "key": "update_key",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_nickname_invalid(self) -> None:
        """유효하지 않은 유저 닉네임"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            reverse("users:user_update_delete"),
            data={"nickname": "안녕"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_nickname_duplicate(self) -> None:
        """닉네임 중복"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            reverse("users:user_update_delete"),
            data={"nickname": "test2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
