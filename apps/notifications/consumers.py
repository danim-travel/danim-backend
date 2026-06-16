import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.core.cache import cache

from apps.notifications.models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user_id = self.scope["url_route"]["kwargs"]["user_id"]

        if not await self.user_exists():
            await self.accept()
            await self.send(json.dumps({"error_detail": "해당 유저를 찾지 못했습니다."}))
            await self.close()
            return

        self.group_name = f"user_{self.user_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        unread_count = await self.get_unread_count()
        await self.send(json.dumps({"unread_count": unread_count}))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_unread_count(self, event):
        await self.send(json.dumps({"unread_count": event["count"]}))

    @database_sync_to_async
    def user_exists(self):
        return User.objects.filter(id=self.user_id).exists()

    @database_sync_to_async
    def get_unread_count(self):
        count = cache.get(f"user_{self.user_id}_unread_count")
        if count is None:
            count = Notification.objects.filter(
                receiver_id=self.user_id, is_read=False
            ).count()
            cache.set(f"user_{self.user_id}_unread_count", count, timeout=None)
        return count
