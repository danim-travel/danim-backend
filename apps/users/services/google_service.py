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


class GoogleService:
    AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    PROFILE_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
    SCOPE = "openid email profile"
    SOCIAL_EMAIL_DOMAIN = "social.danim.kr"
    STATE_TTL = 300

    def build_authorize_url(self) -> str:
        """소셜로그인 url에 담길 정보 생성"""
        state = generate_token()
        cache.set(SocialRedisKey.state(state), True, self.STATE_TTL)

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": self.SCOPE,
            "state": state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def _verify_state(self, state: str) -> None:
        """요청한 데이터에 담긴 redis 키 값 유효성 검증"""
        if not cache.get(SocialRedisKey.state(state)):
            raise ValidationException("유효하지 않은 요청입니다.")
        cache.delete(SocialRedisKey.state(state))

    def _get_google_token(self, code: str) -> str:
        """구글로 부터 jwt 토큰을 가져와 프로필정보를 가져오는 인증장치로 사용"""
        response = httpx.post(
            self.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "code": code,
            },
            timeout=5,
        )
        if response.status_code != 200:
            raise ValidationException("구글 인증에 실패했습니다.")
        return response.json()["access_token"]

    def _get_google_profile(self, access_token: str) -> dict:
        """_get_google_token 함수에서 받아온 access_token으로 구글에 요청을 다시 보내고 프로필 정보를 받아옴"""
        response = httpx.get(
            self.PROFILE_URL,
            headers={
                "Authorization": f"Bearer {access_token}",
            },
            timeout=5,
        )
        if response.status_code != 200:
            raise ValidationException("구글 유저 정보 조회에 실패했습니다.")
        data = response.json()
        return {"social_id": str(data["sub"]), "email": data.get("email")}

    def _issue_jwt(self, user: User) -> tuple[str, str]:
        """우리 홈페이지 jwt 생성"""
        token = RefreshToken.for_user(user)
        token["login_type"] = user.login_type
        return str(token.access_token), str(token)

    def _create_google_user(self, profile: dict) -> User:
        """유저 데이터가 존재하지 않으면 회원가입 시키는 함수"""
        email = (
            profile.get("email")
            or f"google_{profile['social_id']}@{self.SOCIAL_EMAIL_DOMAIN}"
        )
        with transaction.atomic():
            user = User.objects.create_social_user(
                email=email,
                nickname=f"google_{profile['social_id']}",
                name="구글",
                birth_day=date(2000, 1, 1),
                login_type=LoginType.GOOGLE,
                is_active=True,
            )
            SocialAccount.objects.create(
                user=user, login_type=LoginType.GOOGLE, social_id=profile["social_id"]
            )
        return user

    def google_callback(self, code: str, state: str) -> dict:
        """최종적으로 구글과 통신하며 유저가 db에 존재하면 로그인으로 아니면 회원가입시키는 함수"""
        self._verify_state(state)
        access_token = self._get_google_token(code)
        profile = self._get_google_profile(access_token)

        try:
            social = SocialAccount.objects.select_related("user").get(
                login_type=LoginType.GOOGLE, social_id=profile["social_id"]
            )
            user = social.user
        except SocialAccount.DoesNotExist:
            try:
                user = self._create_google_user(profile)
            except IntegrityError:
                user = (
                    SocialAccount.objects.select_related("user")
                    .get(login_type=LoginType.GOOGLE, social_id=profile["social_id"])
                    .user
                )

        access, refresh = self._issue_jwt(user)
        return {
            "access_token": access,
            "refresh_token": refresh,
        }
