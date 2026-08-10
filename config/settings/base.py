from pathlib import Path

import environ
import sentry_sdk
from botocore.config import Config
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / "envs" / ".env")

SECRET_KEY = env("SECRET_KEY")
FRONTEND_URL = env("FRONTEND_URL", default="https://danim.kr")

DJANGO_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # GinIndex(pg_trgm) 사용을 위해 필요
]

THIRD_APPS = [
    "channels",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "corsheaders",
    "storages",
    "drf_spectacular",
]

OWN_APPS: list[str] = [
    "apps.users",
    "apps.posts",
    "apps.comments",
    "apps.follows",
    "apps.blocks",
    "apps.notifications",
    "apps.directmessages",
    "apps.explores",
    "apps.supports",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_APPS + OWN_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Daphne는 static을 서빙하지 않으므로 admin 정적 파일은 whitenoise가 담당
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env("REDIS_URL")],
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True
APPEND_SLASH = False

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Manifest 방식은 collectstatic 누락 시 500을 내므로 압축만 사용(안전 우선).
# 파일 스토리지는 커스텀 S3 서비스(boto3 직접 호출)를 쓰므로 default는 기본값 유지.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
# admin 노출 경로 — 운영/dev는 secrets로 추측 어려운 값 주입.
# 선행 슬래시가 들어오면 path()가 영원히 매치되지 않으므로 앞뒤 슬래시를 정규화한다.
# (운영은 prod.py에서 기본값 admin/이면 부팅 실패로 강제)
ADMIN_URL = (env("ADMIN_URL", default="") or "admin").strip().strip("/") + "/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

# Security Headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# HTTPS 강제와 HSTS는 Django가 아니라 nginx가 담당한다
# (nginx/nginx.conf·nginx.dev.conf — :80은 전부 301, 443에 HSTS 헤더).
#
# W004(HSTS): 여기서 SECURE_HSTS_SECONDS를 켜면 Django와 nginx가 각각 헤더를 붙여
#   중복이 되고, 브라우저는 먼저 오는 값(upstream인 Django 쪽)을 채택해 nginx에
#   적어둔 정책이 조용히 무력화된다(RFC 6797 §8.1). 값을 바꾸려면 nginx를 고칠 것.
# W008(SSL 리다이렉트): 같은 이유다. nginx가 이미 :80을 301로 보내므로 Django의
#   리다이렉트는 도달하지 않는 중복 경로다.
#
# 둘 다 "구현이 없다"가 아니라 "다른 계층이 담당한다"라서 침묵시킨다.
# nginx에서 이 둘을 걷어내게 되면 이 목록도 함께 지워야 한다.
SILENCED_SYSTEM_CHECKS = ["security.W004", "security.W008"]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.core.authentication.JWTAuthenticationNoWWW",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.exception_handler.custom_exception_handler",
    # 스코프별 rate limit — 전역 스로틀은 걸지 않고, 무인증 쓰기 등
    # 필요한 뷰에서만 ScopedRateThrottle + throttle_scope로 선택 적용한다
    "DEFAULT_THROTTLE_RATES": {
        "faq_feedback": "10/min",
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "danim API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
SITE_ID = 1

EMAIL_VERIFY_REDIS_URL = env("REDIS_AUTH_URL")

# 587 안됄경우 465 ssl로 사용가능
# Email
EMAIL_HOST = "smtp.naver.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")

REST_AUTH = {
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "access_token",
    "JWT_AUTH_REFRESH_COOKIE": "refresh_token",
    "TOKEN_MODEL": None,
}

# AWS S3
S3_REGION = env("S3_REGION", default="ap-northeast-2")
S3_ACCESS_KEY_ID = env("S3_ACCESS_KEY_ID", default="AKIADUMMYDUMMYDUMMY1")  # 더미 아이디
S3_SECRET_ACCESS_KEY = env(
    "S3_SECRET_ACCESS_KEY", default="DUMMYSECRETKEYDUMMYSECRETKEYDUMMYSECRET1"
)  # 더미 키
S3_BUCKET_NAME = env("S3_BUCKET_NAME", default="danim_local")
S3_PREFIX = env("S3_PREFIX", default="local/")
S3_PATH = env("S3_PATH", default="{action}/image/{category}/{suffix}")


# Kakao OAuth
KAKAO_REST_API_KEY = env("KAKAO_REST_API_KEY", default="")
KAKAO_CLIENT_SECRET = env("KAKAO_CLIENT_SECRET", default="")
KAKAO_REDIRECT_URI = env("KAKAO_REDIRECT_URI", default="")
FRONT_REDIRECT_URI = env("FRONT_REDIRECT_URI", default="")

# Sentry (DSN이 비어있으면 자동 비활성화 → 로컬/dev/prod 한 곳에서 제어)
SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=env("DJANGO_ENV", default="local"),
        traces_sample_rate=0.1,
        send_default_pii=False,
    )

# 캐시 장애 정책 (이원화 — 용도에 따라 반대 방향이 안전하다):
# - default: 편의 캐시(피드·검색·DM presence·unread). Redis 장애 시 예외를 삼키고
#   miss로 동작(fail-open) — 캐시가 없어도 DB로 서비스가 굴러가야 한다.
# - auth: 보안 키(토큰 블랙리스트·이메일 인증코드·소켓 키). 장애를 삼키면
#   "로그아웃했는데 토큰이 살아있는" fail-open이 되므로 예외를 그대로 던진다(fail-closed).
# ⚠ 환경 파일(dev/prod/local)에서 CACHES를 재정의하지 말 것 — 과거 재정의가
#   IGNORE_EXCEPTIONS를 누락시켜 환경별로 정책이 갈라졌던 이력이 있다.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,
        },
    },
    "auth": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}
# default 별칭이 삼킨 예외는 로그로 남긴다 (조용한 성능 저하의 가시화)
DJANGO_REDIS_LOG_IGNORED_EXCEPTIONS = True

# Google OAuth
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = env("GOOGLE_REDIRECT_URI", default="")

FRONTEND_URL = env("FRONTEND_URL", default="https://danim.kr")

# Celery
CELERY_BROKER_URL = env("REDIS_URL")
CELERY_RESULT_BACKEND = env("REDIS_URL")
CELERY_TIMEZONE = "Asia/Seoul"
CELERY_ENABLE_UTC = False
CELERY_TASK_IGNORE_RESULT = True

CELERY_BEAT_SCHEDULE = {
    "delete-old-notifications": {
        "task": "apps.notifications.tasks.delete_notification_task",
        "schedule": (crontab(hour=3, minute=0)),
    },
}
