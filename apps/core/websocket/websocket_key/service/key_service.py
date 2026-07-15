import uuid

from django.core.cache import caches


def make_socket_key(user):
    socket_key = uuid.uuid4()
    # 소켓 키는 인증 상태 — fail-closed 별칭 사용.
    # default 별칭(IGNORE_EXCEPTIONS=True)이면 Redis 장애 시 저장이 조용히
    # 실패한 키를 클라이언트에 돌려줘, 연결 시 반드시 익명 처리되는 죽은 키가 된다.
    caches["auth"].set(f"socket_key_{socket_key}", user.id, timeout=30)
    return socket_key
