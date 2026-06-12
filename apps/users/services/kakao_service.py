from urllib.parse import urlencode

import httpx
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import ConflictException, ValidationException
from apps.core.utils.base62 import generate_token
from apps.users.models import LoginType, User
from apps.users.models.socialaccount import SocialAccount
from apps.users.redis_keys import SocialRedisKey


class KakaoService:
    """
    카카오 소셜 로그인 (2단계 가입 방식)

    [이메일 처리]
    - 카카오 이메일 동의 시 받은 email 사용, 미제공 시 더미(kakao_{id}@social.danim.kr) 폴백

    [왜 2단계인가]
    - nickname은 영문/숫자/_만 허용 → 카카오 닉네임(한글)을 그대로 못 씀
    - nickname/birth_day가 NOT null인데 카카오가 안 줌
    - 따라서 신규 유저는 nickname/birth_day를 폼으로 입력받아 가입

    [개선 여지]
    - birth_day nullable 완화 + nickname 자동 생성 시 1단계(원클릭) 가입 검토
    """

    AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    PROFILE_URL = "https://kapi.kakao.com/v2/user/me"
    SOCIAL_EMAIL_DOMAIN = "social.danim.kr"

    STATE_TTL = 300
    SIGNUP_TTL = 600

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

    def kakao_callback(self, code: str, state: str) -> dict:
        self._verify_state(state)
        access_token = self._get_kakao_token(code)
        profile = self._get_kakao_profile(access_token)

        try:
            social = SocialAccount.objects.select_related("user").get(
                login_type=LoginType.KAKAO,
                social_id=profile["social_id"],
            )
        except SocialAccount.DoesNotExist:
            signup_token = generate_token()
            cache.set(SocialRedisKey.signup(signup_token), profile, self.SIGNUP_TTL)
            return {"is_new": True, "signup_token": signup_token}

        access, refresh = self._issue_jwt(social.user)
        return {
            "is_new": False,
            "access_token": access,
            "refresh_token": refresh,
        }

    def complete_signup(
        self, signup_token: str, nickname: str, name: str, birth_day
    ) -> tuple[str, str]:
        profile = cache.get(SocialRedisKey.signup(signup_token))
        if not profile:
            raise ValidationException("가입 시간이 만료되었습니다. 다시 시도해주세요.")
        email = (
            profile.get("email")
            or f"kakao_{profile['social_id']}@{self.SOCIAL_EMAIL_DOMAIN}"
        )
        try:
            with transaction.atomic():
                user = User.objects.create_social_user(
                    email=email,
                    nickname=nickname,
                    name=name,
                    birth_day=birth_day,
                    login_type=LoginType.KAKAO,
                    is_active=True,
                )
                SocialAccount.objects.create(
                    user=user,
                    login_type=LoginType.KAKAO,
                    social_id=profile["social_id"],
                )
        except IntegrityError:
            raise ConflictException("이미 가입된 이메일 또는 닉네임 입니다.")
        cache.delete(SocialRedisKey.signup(signup_token))
        return self._issue_jwt(user)
