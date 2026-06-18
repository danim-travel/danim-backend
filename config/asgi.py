import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from apps.core.websocket.middleware import WebsocketMiddleware
from apps.notifications.routing import websocket_urlpatterns as notification_url

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": WebsocketMiddleware(URLRouter(notification_url)),
    }
)
