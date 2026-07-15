from unittest.mock import patch

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
                "key": "local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png",
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
                "key": "local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png",
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
                "key": "local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("intro", serializer.errors)


class UserUpdateResponseSerializerTest(UserBase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    @patch("apps.users.models.models.s3_svc.create_download_presigned_url")
    def test_update_response(self, mock_presigned) -> None:
        """정상적인 응답 데이터"""
        mock_presigned.return_value = (
            "https://bucket.s3.amazonaws.com/local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png?X-Amz-Signature=abc"
        )
        serializer = UserUpdateResponseSerializer(self.user1)
        self.assertEqual(serializer.data["nickname"], "test")
        self.assertEqual(serializer.data["intro"], "test_intro")
        self.assertIn("local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png", serializer.data["profile_img"])
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

    @patch("apps.users.models.models.s3_svc.create_download_presigned_url")
    def test_get_me_info(self, mock_presigned) -> None:
        """GET 요청 응답 성공"""
        mock_presigned.return_value = (
            "https://bucket.s3.amazonaws.com/local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png?X-Amz-Signature=abc"
        )
        serializer = UserInfoResponseSerializer(self.user1)
        self.assertEqual(serializer.data["nickname"], "test")
        self.assertIn("local/upload/image/user/profile/01JZWK7R2MNBX5QD8FHYC3VT9E.png", serializer.data["profile_img"])
        self.assertIn("X-Amz-Signature", serializer.data["profile_img"])
        self.assertEqual(serializer.data["user_id"], self.user1.id)
