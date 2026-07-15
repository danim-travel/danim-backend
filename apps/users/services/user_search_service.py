from django.db.models import QuerySet

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User

# 1자 검색은 trigram 인덱스로도 결과가 폭발한다 (사실상 전 유저 매칭)
MIN_SEARCH_LENGTH = 2


class UserSearchService:

    def search_users(self, search: str) -> QuerySet[User]:
        """닉네임으로 유저를 검색한다.

        - nickname만 매칭한다. name(실명)은 검색 대상이 아니다 — 실명으로
          특정인의 계정을 찾아내는 신원 추적에 악용될 수 있고, 응답에도
          실명은 나가지 않으므로 UX 이득 없이 프라이버시 리스크만 있었다.
        - icontains(중위 검색)는 B-tree를 못 타지만, nickname의
          trigram GIN 인덱스(migration 0008)가 LIKE '%x%'를 가속한다.
        """
        if not search:
            raise ValidationException("검색어를 입력해 주세요.")
        if len(search) < MIN_SEARCH_LENGTH:
            raise ValidationException(
                f"검색어는 {MIN_SEARCH_LENGTH}자 이상 입력해 주세요."
            )
        return User.objects.filter(nickname__icontains=search)
