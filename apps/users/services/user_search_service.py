from django.db.models import Q, QuerySet

from apps.core.exceptions.exception import ValidationException
from apps.users.models import User


class UserSearchService:

    def search_users(self, search: str) -> QuerySet[User]:
        if not search:
            raise ValidationException("검색어를 입력해 주세요.")
        return User.objects.filter(
            Q(nickname__icontains=search) | Q(name__icontains=search)
        )
