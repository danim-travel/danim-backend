import json

from channels.db import database_sync_to_async
from django.core.cache import cache

from apps.core.websocket.base import BaseConsumer
from apps.notifications.models import Notification


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
        count = cache.get(f"user_{self.user.id}_unread_count")
        if count is None:
            count = Notification.objects.filter(
                receiver_id=self.user.id, is_read=False
            ).count()
            cache.set(f"user_{self.user.id}_unread_count", count, timeout=None)
        return count
