from datetime import date
from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import generate_token
from apps.users.models import LoginType, User
from apps.users.models.socialaccount import SocialAccount
from apps.users.redis_keys import SocialRedisKey


class KakaoService:
    """
    카카오 소셜 로그인 (1단계 자동 가입)

    [가입 방식]
    - 신규 유저는 콜백에서 즉시 자동 가입 (추가 폼 없음)
    - nickname/name/birth_day는 자동 기본값 → 가입 후 프로필 수정에서 변경 유도
    - email은 카카오 동의 시 사용, 미제공 시 더미(kakao_{id}@social.danim.kr)

    [한계/개선]
    - nickname/birth_day가 기본값(더미)이라 유저가 프로필에서 수정 필요
    """

    AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    PROFILE_URL = "https://kapi.kakao.com/v2/user/me"
    SOCIAL_EMAIL_DOMAIN = "social.danim.kr"

    STATE_TTL = 300

    def build_authorize_url(self) -> str:
        state = generate_token()
        cache.set(SocialRedisKey.state(state), True, self.STATE_TTL)

        params = {
            "client_id": settings.KAKAO_REST_API_KEY,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def _verify_state(self, state: str) -> None:
        if not cache.get(SocialRedisKey.state(state)):
            raise ValidationException("유효하지 않은 요청입니다.")
        cache.delete(SocialRedisKey.state(state))

    def _get_kakao_token(self, code: str) -> str:
        response = httpx.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_REST_API_KEY,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "redirect_uri": settings.KAKAO_REDIRECT_URI,
                "code": code,
            },
            timeout=5,
        )
        if response.status_code != 200:
            raise ValidationException("카카오 인증에 실패했습니다.")
        return response.json()["access_token"]

    def _get_kakao_profile(self, access_token: str) -> dict:
        response = httpx.get(
            self.PROFILE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=5,
        )
        if response.status_code != 200:
            raise ValidationException("카카오 유저 정보 조회에 실패했습니다.")

        data = response.json()
        account = data["kakao_account"]
        return {"social_id": str(data["id"]), "email": account.get("email")}

    def _issue_jwt(self, user: User) -> tuple[str, str]:
        token = RefreshToken.for_user(user)
        token["login_type"] = user.login_type
        return str(token.access_token), str(token)

    def _create_kakao_user(self, profile: dict) -> User:
        email = (
            profile.get("email")
            or f"kakao_{profile['social_id']}@{self.SOCIAL_EMAIL_DOMAIN}"
        )
        with transaction.atomic():
            user = User.objects.create_social_user(
                email=email,
                nickname=f"kakao_{profile['social_id']}",
                name="카카오",
                birth_day=date(2000, 1, 1),
                login_type=LoginType.KAKAO,
                is_active=True,
            )
            SocialAccount.objects.create(
                user=user,
                login_type=LoginType.KAKAO,
                social_id=profile["social_id"],
            )
        return user

    def kakao_callback(self, code: str, state: str) -> dict:
        self._verify_state(state)
        access_token = self._get_kakao_token(code)
        profile = self._get_kakao_profile(access_token)

        try:
            social = SocialAccount.objects.select_related("user").get(
                login_type=LoginType.KAKAO,
                social_id=profile["social_id"],
            )
            user = social.user
        except SocialAccount.DoesNotExist:
            try:
                user = self._create_kakao_user(profile)
            except IntegrityError:
                user = (
                    SocialAccount.objects.select_related("user")
                    .get(
                        login_type=LoginType.KAKAO,
                        social_id=profile["social_id"],
                    )
                    .user
                )

        access, refresh = self._issue_jwt(user)
        return {
            "access_token": access,
            "refresh_token": refresh,
        }
