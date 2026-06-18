import json

from channels.db import database_sync_to_async
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.storage.s3 import s3_svc
from apps.core.websocket.base import BaseConsumer
from apps.directmessages.models import Conversation, Message
from apps.notifications.utils import create_notification
from apps.users.models import User


class DMConsumer(BaseConsumer):

    async def on_connect(self) -> None:
        self.conversation_id: str = self.scope["url_route"]["kwargs"]["conversation_id"]

        if len(self.conversation_id) != 26:
            await self.send(
                json.dumps({"type": "error", "detail": "잘못된 대화방 ID입니다."})
            )
            await self.close()
            return

        conversation = await self._get_conversation(self.conversation_id, self.user)
        if not conversation:
            await self.send(
                json.dumps({"type": "error", "detail": "대화방을 찾을 수 없습니다."})
            )
            await self.close()
            return

        self.conversation: Conversation = conversation
        self.group_name = f"conversation_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        message_ids = await self._mark_messages_as_read(conversation, self.user)
        if message_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "broadcast_read_receipt", "message_ids": message_ids},
            )

    async def receive(self, text_data: str) -> None:
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        if data.get("type") == "send_message":
            await self._handle_send_message(data)

    async def _handle_send_message(self, data: dict) -> None:
        user: User = self.user  # type: ignore[assignment]
        content: str | None = data.get("content")
        img_key: str | None = data.get("img_key")
        original_img: str | None = data.get("original_img")

        if not content and not img_key:
            return

        message = await self._create_message_and_update_conversation(
            self.conversation, user, content, img_key, original_img
        )

        img_url = s3_svc.create_download_presigned_url(img_key) if img_key else None

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast_receive_message",
                "message_id": str(message.id),
                "sender": {
                    "user_id": str(user.id),
                    "nickname": user.nickname,
                    "profile_img": user.profile_img_url,
                },
                "content": content,
                "img_url": img_url,
                "original_img": original_img,
                "is_read": False,
                "created_at": message.created_at.isoformat(),
            },
        )

        receiver_id = (
            self.conversation.user2_id
            if self.conversation.user1_id == user.id
            else self.conversation.user1_id
        )
        await database_sync_to_async(create_notification)(
            receiver_id=receiver_id,
            sender=user,
            noti_type="dm",
            target_id=str(self.conversation.id),
        )

    async def broadcast_receive_message(self, event: dict) -> None:
        payload = {k: v for k, v in event.items() if k != "type"}
        await self.send(json.dumps({"type": "receive_message", **payload}))

    async def broadcast_read_receipt(self, event: dict) -> None:
        await self.send(
            json.dumps({"type": "read_receipt", "message_ids": event["message_ids"]})
        )

    async def broadcast_message_deleted(self, event: dict) -> None:
        await self.send(
            json.dumps({"type": "message_deleted", "message_id": event["message_id"]})
        )

    @database_sync_to_async
    def _get_conversation(self, conversation_id: str, user: User) -> Conversation | None:
        try:
            return Conversation.objects.get(
                Q(user1=user, user1_left_at__isnull=True)
                | Q(user2=user, user2_left_at__isnull=True),
                pk=conversation_id,
            )
        except (Conversation.DoesNotExist, ValueError):
            return None

    @database_sync_to_async
    def _mark_messages_as_read(self, conv: Conversation, user: User) -> list[str]:
        now = timezone.now()

        if conv.user1_id == user.id:
            last_read_at = conv.user1_last_read_at
            Conversation.objects.filter(pk=conv.id).update(
                user1_last_read_at=now, user1_unread_count=0
            )
        else:
            last_read_at = conv.user2_last_read_at
            Conversation.objects.filter(pk=conv.id).update(
                user2_last_read_at=now, user2_unread_count=0
            )

        qs = Message.objects.filter(conversation=conv).exclude(sender=user)
        if last_read_at:
            qs = qs.filter(created_at__gt=last_read_at)

        return [str(msg_id) for msg_id in qs.values_list("id", flat=True)]

    @database_sync_to_async
    def _create_message_and_update_conversation(
        self,
        conv: Conversation,
        user: User,
        content: str | None,
        img_key: str | None,
        original_img: str | None,
    ) -> Message:
        with transaction.atomic():
            img_url = s3_svc.create_img_url(img_key) if img_key else None
            message = Message.objects.create(
                conversation=conv,
                sender=user,
                content=content,
                img_key=img_key,
                img_url=img_url,
                original_img=original_img,
            )
            now = timezone.now()
            if conv.user1_id == user.id:
                Conversation.objects.filter(pk=conv.id).update(
                    last_message_at=now,
                    user2_unread_count=models.F("user2_unread_count") + 1,
                )
            else:
                Conversation.objects.filter(pk=conv.id).update(
                    last_message_at=now,
                    user1_unread_count=models.F("user1_unread_count") + 1,
                )
            return message
