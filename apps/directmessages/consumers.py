import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db import models
from django.db.models import Q
from django.utils import timezone
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.core.storage.s3 import s3_svc
from apps.directmessages.models import Conversation, Message
from apps.users.models import User

AUTH_TIMEOUT = 10


class DMConsumer(AsyncWebsocketConsumer):

    async def connect(self) -> None:
        self.conversation_id: str = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.authenticated: bool = False
        self.user: User | None = None
        self.conversation: Conversation | None = None
        self.group_name: str | None = None
        await self.accept()
        self._auth_timeout_task = asyncio.create_task(self._close_if_not_authenticated())

    async def disconnect(self, close_code: int) -> None:
        if hasattr(self, "_auth_timeout_task") and not self._auth_timeout_task.done():
            self._auth_timeout_task.cancel()
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data: str) -> None:
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

        if data.get("type") == "send_message":
            await self._handle_send_message(data)

    async def _close_if_not_authenticated(self) -> None:
        await asyncio.sleep(AUTH_TIMEOUT)
        if not self.authenticated:
            await self.close()

    async def _handle_auth(self, data: dict) -> None:
        user = await self._authenticate(data.get("token", ""))
        if not user:
            await self.send(
                json.dumps({"type": "error", "detail": "인증에 실패했습니다."})
            )
            await self.close()
            return

        conversation = await self._get_conversation(self.conversation_id, user)
        if not conversation:
            await self.send(
                json.dumps({"type": "error", "detail": "대화방을 찾을 수 없습니다."})
            )
            await self.close()
            return

        self.user = user
        self.conversation = conversation
        self.authenticated = True
        self._auth_timeout_task.cancel()
        self.group_name = f"conversation_{self.conversation_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        message_ids = await self._mark_messages_as_read(conversation, user)
        if message_ids:
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "broadcast_read_receipt", "message_ids": message_ids},
            )

    async def _handle_send_message(self, data: dict) -> None:
        user: User = self.user  # type: ignore[assignment]
        conversation: Conversation = self.conversation  # type: ignore[assignment]

        content: str | None = data.get("content")
        img_key: str | None = data.get("img_key")
        original_img: str | None = data.get("original_img")

        if not content and not img_key:
            return

        message = await self._create_message(
            conversation, user, content, img_key, original_img
        )
        await self._update_conversation_on_send(conversation, user)

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
    def _authenticate(self, token_str: str) -> User | None:
        try:
            token = AccessToken(token_str)  # type: ignore[arg-type]
            return User.objects.get(id=token["user_id"])
        except (InvalidToken, TokenError, User.DoesNotExist, KeyError):
            return None

    @database_sync_to_async
    def _get_conversation(self, conversation_id: str, user: User) -> Conversation | None:
        try:
            return Conversation.objects.get(
                Q(user1=user, user1_left_at__isnull=True)
                | Q(user2=user, user2_left_at__isnull=True),
                pk=conversation_id,
            )
        except Conversation.DoesNotExist:
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
    def _create_message(
        self,
        conv: Conversation,
        user: User,
        content: str | None,
        img_key: str | None,
        original_img: str | None,
    ) -> Message:
        img_url = s3_svc.create_img_url(img_key) if img_key else None
        return Message.objects.create(
            conversation=conv,
            sender=user,
            content=content,
            img_key=img_key,
            img_url=img_url,
            original_img=original_img,
        )

    @database_sync_to_async
    def _update_conversation_on_send(self, conv: Conversation, user: User) -> None:
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
