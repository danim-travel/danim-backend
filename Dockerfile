FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

# 정적 파일을 이미지에 굽는다 — whitenoise는 부팅 시 1회만 STATIC_ROOT를 스캔하므로
# 배포 스크립트에서 뒤늦게 collectstatic 하면 빈 인덱스로 굳는다(순서 버그).
# 정적 파일은 환경 무관이라 빌드용 더미 env로 충분하다.
RUN SECRET_KEY=build-only \
    REDIS_URL=redis://localhost:6379/0 \
    REDIS_AUTH_URL=redis://localhost:6379/0 \
    DB_NAME=build DB_USER=build DB_PASSWORD=build DB_HOST=localhost \
    uv run --no-sync python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["uv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
