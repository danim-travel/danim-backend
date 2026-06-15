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
