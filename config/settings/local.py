from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

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


EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

SPECTACULAR_SETTINGS["SWAGGER_UI_SETTINGS"] = {"filter": True}


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

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://dev.danim.kr",
    "https://dev-api.danim.kr",
]
CORS_ALLOW_CREDENTIALS = True

SHOW_SWAGGER = True
