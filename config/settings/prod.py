from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT", default="5432"),
    }
}


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True

S3_CONFIG = Config(s3={"addressing_style": "virtual"})

# nginx가 443에서 TLS를 종료하고 http로 프록시하므로, X-Forwarded-Proto를 신뢰해야
# is_secure()가 True가 되어 admin 로그인 등 CSRF Origin 검사가 통과한다.
# (nginx가 이 헤더를 항상 덮어쓰므로 위조 경로 없음 — nginx.conf 참조)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["https://api.danim.kr"])
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# 운영 admin은 추측 어려운 경로가 유일한 노출 방어라, secret 미설정으로
# 기본 admin/에 조용히 열리는 것을 부팅 실패로 막는다.
if ADMIN_URL == "admin/":
    raise ImproperlyConfigured(
        "운영에서는 ADMIN_URL 시크릿을 반드시 설정해야 합니다 (기본 admin/ 금지)."
    )
