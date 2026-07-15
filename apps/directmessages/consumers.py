import asyncio
import json
import logging

from channels.db import database_sync_to_async
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.storage.s3 import s3_svc
from apps.core.websocket.base import BaseConsumer
from apps.directmessages.models import Conversation, Message
from apps.notifications.services.list_service import read_all_about_conversation_dm
from apps.users.models import User

logger = logging.getLogger(__name__)

PRESENCE_TTL = 30
HEARTBEAT_INTERVAL = 20


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

        await self._set_presence(True)
        self._heartbeat_task = asyncio.ensure_future(self._presence_heartbeat())

        message_ids = await self._mark_messages_as_read(conversation, self.user)
        if message_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "broadcast_read_receipt", "message_ids": message_ids},
            )

        try:
            await self._read_dm_notification()
        except Exception as e:
            logger.warning(
                f"[DMConsumer] 알림 읽음 처리 실패 — 연결은 유지: conversation_id={self.conversation_id}, error={e}"
            )

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "_heartbeat_task"):
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        if hasattr(self, "conversation_id"):
            await self._set_presence(False)
        await super().disconnect(close_code)

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

        # 차단 관계면 전송 거부 — 대화 생성은 서비스에서 막지만,
        # 이미 열려 있던 대화방의 소켓으로 계속 보내는 경로가 남는다.
        if await self._is_blocked_conversation(user):
            await self.send(
                json.dumps(
                    {
                        "type": "error",
                        "detail": "차단 관계에서는 메시지를 보낼 수 없습니다.",
                    }
                )
            )
            return

        is_present = await self._is_receiver_present()

        message = await self._create_message_and_update_conversation(
            self.conversation,
            user,
            content,
            img_key,
            original_img,
            increment_unread=not is_present,
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

        if not is_present:
            receiver_id = self._get_receiver_id()
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "send_dm_notification",
                    "sender_id": str(user.id),
                    "sender_nickname": user.nickname,
                    "conversation_id": str(self.conversation_id),
                    "preview": content[:30] if content else "사진을 보냈습니다.",
                },
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
    def _is_blocked_conversation(self, user: User) -> bool:
        from apps.blocks.services import is_blocked_between

        conv = self.conversation
        other_id = conv.user2_id if conv.user1_id == user.id else conv.user1_id
        return is_blocked_between(user.id, other_id)

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
        increment_unread: bool = True,
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
                update_fields: dict = {"last_message_at": now}
                if increment_unread:
                    update_fields["user2_unread_count"] = (
                        models.F("user2_unread_count") + 1
                    )
                Conversation.objects.filter(pk=conv.id).update(**update_fields)
            else:
                update_fields = {"last_message_at": now}
                if increment_unread:
                    update_fields["user1_unread_count"] = (
                        models.F("user1_unread_count") + 1
                    )
                Conversation.objects.filter(pk=conv.id).update(**update_fields)
            return message

    def _get_receiver_id(self) -> str:
        assert self.user is not None
        conv = self.conversation
        return str(conv.user2_id if conv.user1_id == self.user.id else conv.user1_id)

    @database_sync_to_async
    def _set_presence(self, is_present: bool) -> None:
        assert self.user is not None
        key = f"dm_presence_{self.conversation_id}_{self.user.id}"
        if is_present:
            cache.set(key, 1, timeout=PRESENCE_TTL)
        else:
            cache.delete(key)

    @database_sync_to_async
    def _is_receiver_present(self) -> bool:
        receiver_id = self._get_receiver_id()
        key = f"dm_presence_{self.conversation_id}_{receiver_id}"
        return cache.get(key) is not None

    async def _presence_heartbeat(self) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            await self._set_presence(True)

    @database_sync_to_async
    def _read_dm_notification(self) -> None:
        if not self.user:
            return
        read_all_about_conversation_dm(self.user, self.conversation_id)
