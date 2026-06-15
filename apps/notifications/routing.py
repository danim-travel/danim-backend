from django.urls import path

from apps.notifications.consumers import NotificationConsumer

websocket_urlpatterns = [
    path("notifications/<str:user_id>", NotificationConsumer.as_asgi()),
]
