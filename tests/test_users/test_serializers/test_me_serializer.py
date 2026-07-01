from django.test import TestCase

from apps.users.serializers.me_serializer import (
    UserInfoResponseSerializer,
    UserUpdateRequestSerializer,
    UserUpdateResponseSerializer,
)
from tests.test_core.bases.user_base import UserBase


class UserUpdateRequestSerializerTest(TestCase):

    def test_update_request(self) -> None:
        """정상적으로 데이터를 넘겼을떄"""
        serializer = UserUpdateRequestSerializer(
            data={
                "nickname": "test_nickname",
                "intro": "test_intro",
                "key": "test_key",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_update_request_partial_success(self) -> None:
        """부분 수정 — 보낸 필드만 validated_data에 담긴다"""
        serializer = UserUpdateRequestSerializer(
            data={
                "nickname": "test",
            }
        )
        self.assertTrue(serializer.is_valid())
        self.assertIn("nickname", serializer.validated_data)
        self.assertNotIn("intro", serializer.validated_data)
        self.assertNotIn("key", serializer.validated_data)

    def test_update_request_nickname_invalid(self) -> None:
        """닉네임 검증 실패"""
        serializer = UserUpdateRequestSerializer(
            data={
                "nickname": "안녕",
                "intro": "test_intro",
                "key": "test_key",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("nickname", serializer.errors)

    def test_update_request_intro_is_none(self) -> None:
        """intro 가 None 일떄"""
        serializer = UserUpdateRequestSerializer(
            data={
                "nickname": "test_nickname",
                "intro": None,
                "key": "test_key",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("intro", serializer.errors)


class UserUpdateResponseSerializerTest(UserBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_update_response(self) -> None:
        """정상적인 응답 데이터"""
        serializer = UserUpdateResponseSerializer(self.user1)
        self.assertEqual(serializer.data["nickname"], "test")
        self.assertEqual(serializer.data["intro"], "test_intro")
        self.assertIn("test_key", serializer.data["profile_img"])
        self.assertIn("X-Amz-Signature", serializer.data["profile_img"])

    def test_update_response_profile_img_is_none(self) -> None:
        """프로필 이미지를 제외한 수정"""

        serializer = UserUpdateResponseSerializer(self.user2)
        self.assertIsNone(serializer.data["profile_img"])

    def test_update_response_intro_is_none(self) -> None:
        """자기소개글을 제외한 수정"""

        serializer = UserUpdateResponseSerializer(self.user3)
        self.assertIsNone(serializer.data["intro"])


class UserMeInfoResponseSerializerTest(UserBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_get_me_info(self) -> None:
        """GET 요청 응답 성공"""
        serializer = UserInfoResponseSerializer(self.user1)
        self.assertEqual(serializer.data["nickname"], "test")
        self.assertIn("test_key", serializer.data["profile_img"])
        self.assertIn("X-Amz-Signature", serializer.data["profile_img"])
        self.assertEqual(serializer.data["user_id"], self.user1.id)
