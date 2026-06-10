from datetime import date

from django.test import TestCase

from apps.core.storage.s3 import s3_svc
from apps.users.models import User
from apps.users.serializers.me_serializer import (
    UserUpdateRequestSerializer,
    UserUpdateResponseSerializer,
)


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


class UserUpdateResponseSerializerTest(TestCase):
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

    def test_update_response(self) -> None:
        """정상적인 응답 데이터"""
        serializer = UserUpdateResponseSerializer(self.user1)
        self.assertEqual(serializer.data["nickname"], "test")
        self.assertEqual(serializer.data["intro"], "test_intro")
        self.assertEqual(
            serializer.data["profile_img"], s3_svc.create_img_url("test_key")
        )

    def test_update_response_profile_img_is_none(self) -> None:
        """프로필 이미지를 제외한 수정"""

        serializer = UserUpdateResponseSerializer(self.user2)
        self.assertIsNone(serializer.data["profile_img"])

    def test_update_response_intro_is_none(self) -> None:
        """자기소개글을 제외한 수정"""

        serializer = UserUpdateResponseSerializer(self.user3)
        self.assertIsNone(serializer.data["intro"])
