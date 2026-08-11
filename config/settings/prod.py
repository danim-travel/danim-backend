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

# 타임아웃을 명시한다 — 기본값은 connect/read 60초에 재시도 4회라, S3가 늘어지면
# 한 번의 호출이 최대 수분간 호출자를 붙잡는다. 첨부 파기는 solo 워커(순차 처리·
# task_time_limit 미지원)에서 도므로 그동안 같은 큐가 통째로 밀린다.
# 재시도는 태스크 레벨에서 지수 백오프로 한 번 더 감싸므로 여기서는 짧게 둔다.
S3_CONFIG = Config(
    s3={"addressing_style": "virtual"},
    connect_timeout=5,
    read_timeout=10,
    retries={"max_attempts": 2, "mode": "standard"},
)

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
