from datetime import date

from django.test import TestCase

from apps.core.storage.s3 import s3_svc
from apps.users.models import User
from apps.users.models.models import LoginType


class UserTest(TestCase):

    def test_create_user(self) -> None:
        """일반 유저 생성을 위한 test 함수"""
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day=date(1970, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(self.user.nickname, "testnickname")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.name, "test")
        self.assertTrue(self.user.check_password("Password@123"))
        self.assertEqual(self.user.phone_number, "01012345678")
        self.assertEqual(self.user.birth_day, date(1970, 1, 1))
        self.assertTrue(self.user.is_email_verified)
        self.assertTrue(self.user.is_phone_verified)
        self.assertTrue(self.user.is_active)

    def test_create_superuser(self) -> None:
        """superuser을 생성하기 위한 test 함수"""
        self.superuser = User.objects.create_superuser(
            email="super@example.com",
            name="supername",
            nickname="supernickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day=date(1970, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            is_superuser=True,
            login_type=LoginType.EMAIL,
        )
        self.assertTrue(self.superuser.is_staff)
        self.assertTrue(self.superuser.is_superuser)
        self.assertTrue(self.superuser.check_password("Password@123"))


class ProfileImgUrlTest(TestCase):
    """User.profile_img_url 프로퍼티(저장된 S3 key → 조회용 URL 변환) 테스트"""

    def _create_user(self, profile_img: str | None) -> User:
        return User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            birth_day=date(1970, 1, 1),
            profile_img=profile_img,
        )

    def test_returns_url_when_key_exists(self) -> None:
        """profile_img에 key가 있으면 create_img_url로 변환한 URL을 반환한다"""
        key = "local/upload/image/user/profile/01KSHF7EQEGJRVED7VSHJQWBYX.jpg"
        user = self._create_user(profile_img=key)

        self.assertEqual(user.profile_img_url, s3_svc.create_img_url(key))

    def test_returns_none_when_key_is_none(self) -> None:
        """profile_img가 None이면 None을 반환한다"""
        user = self._create_user(profile_img=None)

        self.assertIsNone(user.profile_img_url)

    def test_returns_none_when_key_is_empty(self) -> None:
        """profile_img가 빈 문자열이면 None을 반환한다"""
        user = self._create_user(profile_img="")

        self.assertIsNone(user.profile_img_url)
