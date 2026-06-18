from channels.generic.websocket import AsyncWebsocketConsumer

from apps.users.models import User


class BaseConsumer(AsyncWebsocketConsumer):
    """
    websocket 사용 도메인의 공동 consumer
    def connect -> scope에서 user 뽑고 None이면 close, 인증 성공 시 on_connect 호출
    def on_connect -> 반드시 오버라이드 필요, 구현하지 않으면 NotImplementedError 발생
    def disconnect -> 기존에 생성했던 group 삭제
    """

    user: User | None

    async def connect(self):
        self.user = self.scope.get("user")
        if not self.user.is_authenticated:
            await self.close()
            return

        await self.accept()
        await self.on_connect()

    async def on_connect(self):
        raise NotImplementedError

    async def disconnect(self, close_code):
        if hasattr(self, "group_name") and self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
