import httpx
from django.core.cache import cache
from apps.users.models import User, LoginType
from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import generate_token
from apps.users.redis_keys import SocialRedisKey
from django.conf import settings
from urllib.parse import urlencode
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.models.socialaccount import SocialAccount

class KakaoService:
    AUTHORIZE_URL = "https://kauth.kakao.com/oauth/authorize"
    TOKEN_URL = "https://kauth.kakao.com/oauth/token"
    PROFILE_URL = "https://kapi.kakao.com/v2/user/me"

    STATE_TTL = 300
    SIGNUP_TTL = 600

    def build_authorize_url(self)->str:
        state = generate_token()
        cache.set(SocialRedisKey.state(state),True,self.STATE_TTL)

        params = {
            "client_id":settings.KAKAO_REST_API_KEY,
            "redirect_uri":settings.KAKAO_REDIRECT_URI,
            "response_type":"code",
            "state":state,
        }
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"

    def _verify_state(self,state:str)->None:
        if not cache.get(SocialRedisKey.state(state)):
            raise ValidationException("유효하지 않은 요청입니다.")
        cache.delete(SocialRedisKey.state(state))

    def _get_kakao_token(self,code:str)->str:
        response = httpx.post(
            self.TOKEN_URL,
            data = {
                "grant_type":"authorization_code",
                "client_id":settings.KAKAO_REST_API_KEY,
                "redirect_uri":settings.KAKAO_REDIRECT_URI,
                "code":code
            },
            timeout=5
        )
        if response.status_code != 200:
            raise ValidationException("카카오 인증에 실패했습니다.")
        return response.json()["access_token"]

    def _get_kakao_profile(self,access_token:str)->dict:
        response = httpx.get(
            self.PROFILE_URL,
            headers = {"Authorization": f"Bearer {access_token}"},
            timeout=5
        )
        if response.status_code != 200:
            raise ValidationException("카카오 유저 정보 조회에 실패했습니다.")

        data = response.json()
        account = data["kakao_account"]
        return {
            "social_id": str(data["id"]),
            "email": account.get("email")
        }

    def _issue_jwt(self,user:User)->tuple[str,str]:
        token = RefreshToken.for_user(user)
        token["login_type"] = user.login_type
        return str(token.access_token),str(token)

    def kakao_callback(self,code:str,state:str)->dict:
        self._verify_state(state)
        access_token = self._get_kakao_token(code)
        profile = self._get_kakao_profile(access_token)

        try:
            social = SocialAccount.objects.select_related("user").get(
                login_type= LoginType.KAKAO,
                social_id = profile["social_id"],
            )
        except SocialAccount.DoesNotExist:
            signup_token = generate_token()
            cache.set(SocialRedisKey.signup(signup_token), profile, self.SIGNUP_TTL)
            return {"is_new":True,"signup_token":signup_token}

        access_token,refresh_token = self._issue_jwt(social.user)
        return {
            "is_new":False,
            "access_token":access_token,
            "refresh_token":refresh_token,
        }




