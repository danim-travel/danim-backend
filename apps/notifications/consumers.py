import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.notifications.models import Notification

User = get_user_model()

AUTH_TIMEOUT = 10


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = None
        self.authenticated = False
        self.group_name = None
        await self.accept()
        self._auth_timeout_task = asyncio.create_task(self._close_if_not_authenticated())

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if not self.authenticated:
            if data.get("type") == "auth":
                await self._handle_auth(data)
            else:
                await self.close()
            return

    async def disconnect(self, close_code):
        if hasattr(self, "_auth_timeout_task") and not self._auth_timeout_task.done():
            self._auth_timeout_task.cancel()
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_unread_count(self, event):
        await self.send(json.dumps({"unread_count": event["count"]}))

    async def _close_if_not_authenticated(self):
        await asyncio.sleep(AUTH_TIMEOUT)
        if not self.authenticated:
            await self.close()

    async def _handle_auth(self, data):
        user = await self._authenticate(data.get("token", ""))
        if not user:
            await self.send(
                json.dumps({"type": "error", "detail": "인증에 실패했습니다."})
            )
            await self.close()
            return

        self.user_id = user.id
        self.authenticated = True
        self._auth_timeout_task.cancel()
        self.group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        unread_count = await self.get_unread_count()
        await self.send(json.dumps({"unread_count": unread_count}))

    @database_sync_to_async
    def _authenticate(self, token):
        try:
            token = AccessToken(token)
            return User.objects.get(id=token["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
            return None

    @database_sync_to_async
    def get_unread_count(self):
        count = cache.get(f"user_{self.user_id}_unread_count")
        if count is None:
            count = Notification.objects.filter(
                receiver_id=self.user_id, is_read=False
            ).count()
            cache.set(f"user_{self.user_id}_unread_count", count, timeout=None)
        return count
