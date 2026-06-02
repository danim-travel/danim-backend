from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions.exception import ForbiddenException


class TokenService:

    def refresh_access_token(self, refresh_token: str) -> str:
        try:
            token = RefreshToken(refresh_token)  # type: ignore[arg-type]
            return str(token.access_token)
        except TokenError:
            raise ForbiddenException("로그인 세션이 만료되었습니다.")
