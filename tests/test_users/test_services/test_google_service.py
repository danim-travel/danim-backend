from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User
from apps.users.models.models import LoginType
from apps.users.models.socialaccount import SocialAccount
from apps.users.services.google_service import GoogleService


class GoogleServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = GoogleService()

        # 구글 API 호출(httpx) mock
        self.httpx_patcher = patch("apps.users.services.google_service.httpx")
        self.mock_httpx = self.httpx_patcher.start()
        self.addCleanup(self.httpx_patcher.stop)

        # state 검증(cache) mock
        self.cache_patcher = patch("apps.users.services.google_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)
        self.mock_cache.get.return_value = True  # state 검증 통과(기본)

    def _set_google_response(
        self,
        sub="110248495921238986420",
        email="google@test.com",
        token_status=200,
        profile_status=200,
    ):
        """구글 토큰/프로필 응답을 가짜로 세팅"""
        token_resp = MagicMock(status_code=token_status)
        token_resp.json.return_value = {"access_token": "fake_token"}

        profile_resp = MagicMock(status_code=profile_status)
        profile_resp.json.return_value = {"sub": sub, "email": email}

        self.mock_httpx.post.return_value = token_resp  # 토큰 교환
        self.mock_httpx.get.return_value = profile_resp  # 유저정보

    def test_new_user_auto_signup(self):
        """신규 유저 → 즉시 자동 가입 + User/SocialAccount 생성"""
        self._set_google_response(sub="110248495921238986420", email="new@test.com")

        result = self.service.google_callback("code", "state")

        self.assertEqual(User.objects.filter(login_type=LoginType.GOOGLE).count(), 1)
        user = User.objects.get(login_type=LoginType.GOOGLE)
        self.assertEqual(user.nickname, "google_1102484959")  # sub 앞 10자
        self.assertEqual(user.name, "구글")
        self.assertEqual(user.email, "new@test.com")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(
            SocialAccount.objects.filter(
                login_type=LoginType.GOOGLE, social_id="110248495921238986420"
            ).exists()
        )
        self.assertIn("access_token", result)
        self.assertIn("refresh_token", result)

    def test_existing_user_login_no_duplicate(self):
        """기존 유저 → 가입 없이 로그인 (유저 수 안 늘어남)"""
        self._set_google_response(sub="999888777666", email="exist@test.com")
        self.service.google_callback("code", "state")  # 최초 가입
        before = User.objects.filter(login_type=LoginType.GOOGLE).count()

        result = self.service.google_callback("code", "state")  # 같은 sub 재로그인
        after = User.objects.filter(login_type=LoginType.GOOGLE).count()

        self.assertEqual(before, 1)
        self.assertEqual(after, 1)
        self.assertIn("access_token", result)

    def test_invalid_state_raises(self):
        """state가 Redis에 없으면 ValidationException"""
        self.mock_cache.get.return_value = None
        with self.assertRaises(ValidationException):
            self.service.google_callback("code", "bad_state")

    def test_token_exchange_fail_raises(self):
        """구글 토큰 교환 실패(비200) → ValidationException"""
        self._set_google_response(token_status=401)
        with self.assertRaises(ValidationException):
            self.service.google_callback("code", "state")

    def test_profile_fetch_fail_raises(self):
        """구글 유저정보 조회 실패(비200) → ValidationException"""
        self._set_google_response(profile_status=401)
        with self.assertRaises(ValidationException):
            self.service.google_callback("code", "state")

    # def test_email_fallback_to_dummy(self):
    #     """구글이 이메일을 안 주면 더미 이메일로 가입"""
    #     self._set_google_response(sub="123123123123", email=None)
    #
    #     self.service.google_callback("code", "state")
    #
    #     user = User.objects.get(login_type=LoginType.GOOGLE)
    #     self.assertEqual(user.email, "google_123123123123@social.danim.kr")

    def test_build_authorize_url(self):
        """authorize URL에 필수 파라미터(scope 포함) + state 저장"""
        url = self.service.build_authorize_url()

        self.assertIn("accounts.google.com/o/oauth2/v2/auth", url)
        self.assertIn("client_id=", url)
        self.assertIn("redirect_uri=", url)
        self.assertIn("scope=", url)
        self.assertIn("state=", url)
        self.mock_cache.set.assert_called_once()


#
