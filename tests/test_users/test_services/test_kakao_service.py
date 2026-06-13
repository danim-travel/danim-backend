from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User
from apps.users.models.models import LoginType
from apps.users.models.socialaccount import SocialAccount
from apps.users.services.kakao_service import KakaoService


class KakaoServiceTest(TestCase):

    def setUp(self) -> None:
        self.service = KakaoService()

        # 카카오 API 호출(httpx) mock
        self.httpx_patcher = patch("apps.users.services.kakao_service.httpx")
        self.mock_httpx = self.httpx_patcher.start()
        self.addCleanup(self.httpx_patcher.stop)

        # state 검증(cache) mock
        self.cache_patcher = patch("apps.users.services.kakao_service.cache")
        self.mock_cache = self.cache_patcher.start()
        self.addCleanup(self.cache_patcher.stop)
        self.mock_cache.get.return_value = True  # state 검증 통과(기본)

    def _set_kakao_response(
        self,
        social_id=111,
        email="kakao@test.com",
        token_status=200,
        profile_status=200,
    ):
        """카카오 토큰/프로필 응답을 가짜로 세팅"""
        token_resp = MagicMock(status_code=token_status)
        token_resp.json.return_value = {"access_token": "fake_token"}

        account = {"email": email} if email is not None else {}
        profile_resp = MagicMock(status_code=profile_status)
        profile_resp.json.return_value = {"id": social_id, "kakao_account": account}

        self.mock_httpx.post.return_value = token_resp  # 토큰 교환
        self.mock_httpx.get.return_value = profile_resp  # 유저정보

    def test_new_user_auto_signup(self):
        """신규 유저 → 즉시 자동 가입 + User/SocialAccount 생성"""
        self._set_kakao_response(social_id=111, email="new@test.com")

        result = self.service.kakao_callback("code", "state")

        self.assertEqual(User.objects.filter(login_type=LoginType.KAKAO).count(), 1)
        user = User.objects.get(login_type=LoginType.KAKAO)
        self.assertEqual(user.nickname, "kakao_111")
        self.assertEqual(user.name, "카카오")
        self.assertEqual(user.email, "new@test.com")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(
            SocialAccount.objects.filter(
                login_type=LoginType.KAKAO, social_id="111"
            ).exists()
        )
        self.assertIn("access_token", result)
        self.assertIn("refresh_token", result)

    def test_existing_user_login_no_duplicate(self):
        """기존 유저 → 가입 없이 로그인 (유저 수 안 늘어남)"""
        self._set_kakao_response(social_id=222, email="exist@test.com")
        self.service.kakao_callback("code", "state")  # 최초 가입
        before = User.objects.filter(login_type=LoginType.KAKAO).count()

        result = self.service.kakao_callback("code", "state")  # 같은 social_id 재로그인
        after = User.objects.filter(login_type=LoginType.KAKAO).count()

        self.assertEqual(before, 1)
        self.assertEqual(after, 1)
        self.assertIn("access_token", result)

    def test_invalid_state_raises(self):
        """state가 Redis에 없으면 ValidationException"""
        self.mock_cache.get.return_value = None
        with self.assertRaises(ValidationException):
            self.service.kakao_callback("code", "bad_state")

    def test_token_exchange_fail_raises(self):
        """카카오 토큰 교환 실패(비200) → ValidationException"""
        self._set_kakao_response(token_status=401)
        with self.assertRaises(ValidationException):
            self.service.kakao_callback("code", "state")

    def test_profile_fetch_fail_raises(self):
        """카카오 유저정보 조회 실패(비200) → ValidationException"""
        self._set_kakao_response(profile_status=401)
        with self.assertRaises(ValidationException):
            self.service.kakao_callback("code", "state")

    def test_email_fallback_to_dummy(self):
        """카카오가 이메일을 안 주면 더미 이메일로 가입"""
        self._set_kakao_response(social_id=333, email=None)

        self.service.kakao_callback("code", "state")

        user = User.objects.get(login_type=LoginType.KAKAO)
        self.assertEqual(user.email, "kakao_333@social.danim.kr")

    def test_build_authorize_url(self):
        """authorize URL에 필수 파라미터 포함 + state 저장"""
        url = self.service.build_authorize_url()

        self.assertIn("kauth.kakao.com/oauth/authorize", url)
        self.assertIn("client_id=", url)
        self.assertIn("redirect_uri=", url)
        self.assertIn("state=", url)
        self.mock_cache.set.assert_called_once()
