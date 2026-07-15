import logging
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.core.cache import caches
from redis import RedisError

from apps.users.models import User

logger = logging.getLogger(__name__)


async def get_user(user_id):
    return await sync_to_async(User.objects.filter(id=user_id).first)()


class WebsocketMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            query_string = scope.get("query_string", b"").decode()
            socket_key = parse_qs(query_string).get("socket_key", [None])[0]

            # 소켓 키는 인증 상태 — fail-closed 별칭 사용.
            # Redis 장애 시 키를 검증할 수 없으므로 익명 처리(=BaseConsumer가
            # 연결 거부). 장애를 삼키고 익명으로 조용히 통과시키는 것과 결과는
            # 같지만, 여기서는 명시적으로 잡아 로그를 남긴다.
            auth_cache = caches["auth"]
            try:
                user_id = await sync_to_async(auth_cache.get)(
                    f"socket_key_{socket_key}"
                )
                if user_id:
                    await sync_to_async(auth_cache.delete)(
                        f"socket_key_{socket_key}"
                    )
                    scope["user"] = await get_user(user_id)
                else:
                    scope["user"] = AnonymousUser()
            except RedisError:
                logger.warning("[WS] 소켓 키 검증 실패(Redis 장애) — 연결 거부")
                scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
