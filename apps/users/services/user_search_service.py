from django.db.models import QuerySet

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User

# 최소 검색어 길이. 1자는 사실상 전 유저 매칭이라 거부한다.
# ⚠ 알려진 트레이드오프: pg_trgm은 패턴에 연속 3자 이상이 있어야 GIN 인덱스를
# 태운다 — 2자 검색은 인덱스 미가속(스캔 폴백)이다. 그럼에도 2를 유지하는 이유는
# 한글 닉네임의 2자 검색 UX 때문. 유저 테이블이 커져 2자 검색이 병목이 되면
# 3으로 올리거나 2자 전용 prefix 분기를 도입할 것.
MIN_SEARCH_LENGTH = 2


class UserSearchService:

    def search_users(self, search: str) -> QuerySet[User]:
        """닉네임으로 유저를 검색한다.

        - nickname만 매칭한다. name(실명)은 검색 대상이 아니다 — 실명으로
          특정인의 계정을 찾아내는 신원 추적에 악용될 수 있고, 응답에도
          실명은 나가지 않으므로 UX 이득 없이 프라이버시 리스크만 있었다.
        - icontains(중위 검색)는 B-tree를 못 타지만, nickname의
          trigram GIN 인덱스(migration 0008)가 3자 이상 검색어의
          LIKE '%x%'를 가속한다 (2자는 위 상수 주석의 트레이드오프 참조).
        """
        if not search:
            raise ValidationException("검색어를 입력해 주세요.")
        if len(search) < MIN_SEARCH_LENGTH:
            raise ValidationException(
                f"검색어는 {MIN_SEARCH_LENGTH}자 이상 입력해 주세요."
            )
        return User.objects.filter(nickname__icontains=search)
