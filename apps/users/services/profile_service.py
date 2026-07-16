from django.db.models import Count, Exists, IntegerField, OuterRef, QuerySet, Subquery
from django.db.models.functions import Coalesce

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.posts.models import Post
from apps.users.models import User


def _correlated_count(queryset: QuerySet, group_field: str) -> Coalesce:
    """OuterRef 상관 카운트 서브쿼리 (조인 없이 집계).

    Count(..., distinct=True) 3개를 한 쿼리에 annotate하면 reverse FK
    LEFT JOIN 3개가 곱해져 중간 행수가 팔로워수 × 팔로잉수 × 게시글수로
    폭발한다 — 프로필은 가장 자주 열리는 화면이라 치명적.
    서브쿼리로 분리하면 각 카운트가 독립 인덱스 스캔 1번씩이다.
    """
    return Coalesce(
        Subquery(
            queryset.order_by().values(group_field).annotate(c=Count("pk")).values("c"),
            output_field=IntegerField(),
        ),
        0,
    )


class ProfileService:

    def get_profile(self, user_id: str, request_user: User) -> User:
        user = (
            User.objects.annotate(
                follower_count=_correlated_count(
                    Follows.objects.filter(following=OuterRef("pk")), "following"
                ),
                following_count=_correlated_count(
                    Follows.objects.filter(follower=OuterRef("pk")), "follower"
                ),
                posts_count=_correlated_count(
                    Post.objects.filter(user=OuterRef("pk")), "user"
                ),
                is_following=Exists(
                    Follows.objects.filter(
                        follower=request_user,
                        following=OuterRef("pk"),
                    )
                ),
            )
            .filter(id=user_id)
            .first()
        )
        if not user:
            raise NotFoundException("존재하지 않는 유저입니다.")
        return user
