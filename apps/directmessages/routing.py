from django.urls import path

from apps.directmessages.consumers import DMConsumer

websocket_urlpatterns = [
    path("ws/conversations/<str:conversation_id>", DMConsumer.as_asgi()),
]
