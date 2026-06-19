from datetime import date

from apps.posts.models import Post
from apps.users.models import LoginType, User


def user_and_post():
    user = User.objects.create(
        email="test@example.com",
        name="test",
        nickname="testnickname",
        password="Password@123",
        phone_number="01012345678",
        birth_day=date(1970, 1, 1),
        is_email_verified=True,
        is_phone_verified=True,
        is_active=True,
        login_type=LoginType.EMAIL,
    )
    post = Post.objects.create(
        user=user,
        title="testtitle",
        description="testdescription",
        thumbnail="prod/posts/thumbnail/uuid.jpg",
    )
    return user, post


def user_and_posts():
    user = User.objects.create(
        email="test@example.com",
        name="test",
        nickname="testnickname",
        password="Password@123",
        phone_number="01012345678",
        birth_day=date(1970, 1, 1),
        is_email_verified=True,
        is_phone_verified=True,
        is_active=True,
        login_type=LoginType.EMAIL,
    )
    posts = []
    for i in range(25):
        post = Post.objects.create(
            user=user,
            title="testtitle",
            description="testdescription",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        posts.append(post)
    return user, posts


"""apps.explores.services.order 테스트용 헬퍼.

핵심 제어 포인트:
- created_at: auto_now_add 라서 생성 후 .update() 로만 과거로 박을 수 있다.
- random_score: default=_get_random(0~1) 이지만, 풀 구성을 결정적으로 만들기 위해
  테스트에서는 항상 명시적으로 덮어쓴다.
- order 로직은 user 별 필터를 하지 않으므로 모든 post 가 user 1명을 공유해도 된다.
"""

from datetime import timedelta

from django.utils import timezone

from apps.explores.dtos import TasteProfile
from apps.posts.models import Post, PostRec
from tests.test_explores.utils import user_and_post


def make_shared_user():
    """unique 제약(email/nickname/phone) 때문에 user 는 한 번만 만들어 공유한다."""
    user, first_post = user_and_post()
    # 깔끔한 통제를 위해 팩토리가 끼워 만든 post 는 지우고, 테스트에서 직접 찍는다.
    first_post.delete()
    return user


def make_post(
    user,
    *,
    days_ago=0,
    random_score=0.5,
    like_count=0,
    comment_count=0,
    view_count=0,
):
    """created_at 을 days_ago 만큼 과거로, random_score 등을 통제값으로 박은 Post 생성."""
    post = Post.objects.create(
        user=user,
        title="t",
        description="d",
        thumbnail="prod/posts/thumbnail/x.jpg",
        like_count=like_count,
        comment_count=comment_count,
        view_count=view_count,
    )
    created_at = timezone.now() - timedelta(days=days_ago)
    # auto_now_add + random_score 자동 default 를 한 번에 통제값으로 덮어쓴다.
    Post.objects.filter(pk=post.pk).update(
        created_at=created_at, random_score=random_score
    )
    post.refresh_from_db()
    return post


def make_rec(post, codewords, version="v1"):
    """post 에 PostRec(개인화 임베딩) 연결. codewords=[{"codeword": int, "weight": float}, ...]"""
    return PostRec.objects.create(
        post=post, codewords=codewords, codebook_version=version
    )


def taste_profile(counts, *, version="v1", alpha=1.0):
    """UserTaste/taste.py 를 거치지 않고 TasteProfile 을 직접 주입.

    counts 키는 문자열이어야 한다(_post_affinity 가 str(codeword) 로 조회).
    norm 은 from_taste 와 동일하게 L2 노름으로 계산해 둔다.
    """
    norm = (sum(float(v) * float(v) for v in counts.values())) ** 0.5 if counts else 0.0
    return TasteProfile(counts=counts, version=version, alpha=alpha, norm=norm)


def empty_profile():
    """개인화 비활성(active=False) 프로파일."""
    return TasteProfile()
