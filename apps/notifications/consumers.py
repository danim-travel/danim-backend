import json

from channels.db import database_sync_to_async
from django.core.cache import cache

from apps.core.websocket.base import BaseConsumer
from apps.notifications.utils.create_notification import CACHE_UNREAD_TIMEOUT
from apps.users.models import User


class NotificationConsumer(BaseConsumer):

    async def on_connect(self):
        if not self.user.is_authenticated:
            await self.close()
            return
        self.group_name = f"user_{self.user.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        unread_count = await self.get_unread_count()
        await self.send(json.dumps({"unread_count": unread_count}))

    async def send_unread_count(self, event):
        await self.send(json.dumps({"unread_count": event["count"]}))

    @database_sync_to_async
    def get_unread_count(self):
        cache_key = f"user_{self.user.id}_unread_count"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        count = (
            User.objects.filter(id=self.user.id)
            .values_list("unread_noti_count", flat=True)
            .first()
            or 0
        )
        cache.set(cache_key, count, timeout=CACHE_UNREAD_TIMEOUT)
        return count

    async def send_dm_notification(self, event: dict) -> None:
        payload = {k: v for k, v in event.items() if k != "type"}
        await self.send(json.dumps({"type": "dm_notification", **payload}))
