from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.postgres.indexes import GinIndex
from django.db import models

from apps.core.models import TimeStampModel
from apps.core.storage.s3 import s3_svc


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """일반 유저 생성"""
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """super_user 생성.

        is_active 기본값이 False(가입 플로우 전제)라 명시적으로 켜지 않으면
        createsuperuser로 만든 관리자가 admin 로그인에서 거부된다.
        """
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email, password=password, **extra_fields)

    def create_social_user(self, email, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_unusable_password()
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
    unread_noti_count = models.PositiveIntegerField(default=0)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "nickname",
        "name",
        "birth_day",
    ]

    objects = UserManager()

    class Meta:
        db_table = "users"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(unread_noti_count__gte=0),
                name="unread_noti_count_non_negative",
            )
        ]
        indexes = [
            # 유저 검색(nickname__icontains)용 trigram GIN.
            # 중위 LIKE('%x%')는 nickname의 unique B-tree를 못 타 풀스캔이었다.
            # pg_trgm 확장은 posts 0008(TrigramExtension)에서 이미 활성화됨.
            GinIndex(
                fields=["nickname"],
                opclasses=["gin_trgm_ops"],
                name="ix_users_nickname_trgm",
            ),
        ]

    @property
    def profile_img_url(self) -> str | None:
        """저장된 profile_img(S3 key)를 조회용 URL로 변환. key가 없으면 None."""
        if not self.profile_img:
            return None

        return s3_svc.create_download_presigned_url(self.profile_img)
