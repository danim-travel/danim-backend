from apps.core.exceptions.exception import ForbiddenException, ValidationException
from apps.users.models import LoginType, User
from apps.users.services.login_logout_service import _blacklist_refresh_token


class ChangePasswordService:

    def change_password(
        self, user: User, password: str, new_password: str, refresh_token: str
    ) -> None:
        if not user.login_type == LoginType.EMAIL:
            raise ForbiddenException("소셜 로그인 유저는 비밀번호를 변경할 수 없습니다.")
        if not user.check_password(password):
            raise ValidationException("현재 비밀번호가 틀립니다.")

        user.set_password(new_password)
        user.save(update_fields=["password"])
        _blacklist_refresh_token(refresh_token)
