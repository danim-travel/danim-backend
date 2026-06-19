from datetime import date, timedelta

from django.utils import timezone

from apps.explores.dtos import TasteProfile
from apps.posts.models import Post, PostRec
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


def make_shared_user():
    user, first_post = user_and_post()
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
    Post.objects.filter(pk=post.pk).update(
        created_at=created_at, random_score=random_score
    )
    post.refresh_from_db()
    return post


def make_rec(post, codewords, version="v1"):
    return PostRec.objects.create(
        post=post, codewords=codewords, codebook_version=version
    )


def taste_profile(counts, *, version="v1", alpha=1.0):

    norm = (sum(float(v) * float(v) for v in counts.values())) ** 0.5 if counts else 0.0
    return TasteProfile(counts=counts, version=version, alpha=alpha, norm=norm)


def empty_profile():
    return TasteProfile()
