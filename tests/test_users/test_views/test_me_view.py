from datetime import date

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

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
            phone_number="01012345678",
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
            reverse("users:me"),
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
        self.assertIn("update_key", response.data["profile_img"])
        self.assertIn("X-Amz-Signature", response.data["profile_img"])

    def test_user_not_unauthorized(self) -> None:
        """비 로그인 유저가 업데이트 보낼떄 (401)"""
        response = self.client.patch(
            reverse("users:me"),
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
            reverse("users:me"),
            data={"nickname": "안녕"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_nickname_duplicate(self) -> None:
        """닉네임 중복"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            reverse("users:me"),
            data={"nickname": "test2"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)


class UserInfoViewTest(BaseTestCase):

    def test_user_info(self) -> None:
        """내 정보 조회 성공"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(
            reverse("users:me"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["nickname"], self.user1.nickname)
        self.assertIn("test_key", response.data["profile_img"])
        self.assertIn("X-Amz-Signature", response.data["profile_img"])
        self.assertEqual(response.data["user_id"], self.user1.id)
        self.assertEqual(response.data["email"], self.user1.email)
        self.assertEqual(response.data["name"], self.user1.name)
        self.assertEqual(response.data["birth_day"], str(self.user1.birth_day))
        self.assertEqual(response.data["phone_number"], self.user1.phone_number)
        self.assertEqual(response.data["intro"], self.user1.intro)

    def test_user_info_unauthenticated(self) -> None:
        """인증 없이 요청 시 401"""
        response = self.client.get(reverse("users:me"), format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserDeleteViewTest(BaseTestCase):

    def test_delete_success(self) -> None:
        """회원탈퇴 성공 (204) 및 DB에서 삭제 확인"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(
            reverse("users:me"),
            data={"password": "Password@1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(id=self.user1.id).exists())

    def test_delete_wrong_password(self) -> None:
        """비밀번호 불일치 (401), 유저는 삭제되지 않음"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(
            reverse("users:me"),
            data={"password": "WrongPassword@1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(User.objects.filter(id=self.user1.id).exists())

    def test_delete_no_password(self) -> None:
        """비밀번호 미입력 (400), 유저는 삭제되지 않음"""
        self.client.force_authenticate(user=self.user1)
        response = self.client.delete(
            reverse("users:me"),
            data={},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(User.objects.filter(id=self.user1.id).exists())

    def test_delete_unauthenticated(self) -> None:
        """인증 없이 요청 시 (401)"""
        response = self.client.delete(
            reverse("users:me"),
            data={"password": "Password@1"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
