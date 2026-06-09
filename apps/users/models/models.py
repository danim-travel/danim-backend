from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from apps.core.models import BaseModel, TimeStampModel
from apps.core.storage.s3 import s3_svc
from apps.posts.models import Post


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """일반 유저 생성"""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """super_user 생성"""
        email = self.normalize_email(email)
        user = self.create_user(email, password=password, **extra_fields)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class LoginType(models.TextChoices):
    EMAIL = "email"
    KAKAO = "kakao"
    GOOGLE = "google"


class User(AbstractBaseUser, PermissionsMixin, TimeStampModel):
    login_type = models.CharField(
        max_length=10, choices=LoginType.choices, default=LoginType.EMAIL
    )
    email = models.EmailField(max_length=255, unique=True)
    nickname = models.CharField(null=False, unique=True, max_length=20)
    name = models.CharField(null=False, max_length=20)
    phone_number = models.CharField(null=True, max_length=11)
    birth_day = models.DateField(null=False, blank=False)
    profile_img = models.TextField(null=True, blank=True)
    intro = models.CharField(null=True, max_length=100)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "nickname",
        "name",
        "birth_day",
    ]

    objects = UserManager()

    class Meta:
        db_table = "users"

    @property
    def profile_img_url(self) -> str | None:
        """저장된 profile_img(S3 key)를 조회용 URL로 변환. key가 없으면 None."""
        if not self.profile_img:
            return None

        return s3_svc.create_img_url(self.profile_img)


class Follows(BaseModel):
    follower = models.ForeignKey(User, related_name="followers", on_delete=models.CASCADE)
    following = models.ForeignKey(
        User, related_name="following", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "follows"
        unique_together = (("follower", "following"),)


class BookMark(BaseModel):
    post = models.ForeignKey(Post, related_name="bookmarks", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="bookmarks", on_delete=models.CASCADE)

    class Meta:
        db_table = "bookmarks"
        unique_together = (("post", "user"),)
