from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from django.core.cache import cache

from apps.users.models import User


async def get_user(user_id):
    return await sync_to_async(User.objects.filter(id=user_id).first)()


class WebsocketMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            query_string = scope.get("query_string", b"").decode()
            socket_key = parse_qs(query_string).get("socket_key", [None])[0]

            user_id = await sync_to_async(cache.get)(f"socket_key_{socket_key}")
            if user_id:
                await sync_to_async(cache.delete)(f"socket_key_{socket_key}")
                scope["user"] = await get_user(user_id)
            else:
                scope["user"] = None

        return await self.app(scope, receive, send)
