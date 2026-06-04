from apps.core.exceptions.exception import ConflictException
from apps.users.models import User


class CheckNicknameService:

    def check_duplicate_nickname(self, nickname: str) -> str:
        """닉네임 중복 검증"""
        if User.objects.filter(nickname=nickname).exists():
            raise ConflictException("이미 존재하는 닉네임 입니다.")
        return nickname
