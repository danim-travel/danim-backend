from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.websocket.websocket_key.view import WebSocketKey


def hello(request):
    return JsonResponse({"hello": True})


urlpatterns = [
    # admin 경로는 환경변수로 관리 (기본 admin/, 운영은 secrets로 변경)
    path(settings.ADMIN_URL, admin.site.urls),
    path("api/v1/users", include("apps.users.urls", namespace="users")),
    path("api/v1/comments", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts", include("apps.posts.urls", namespace="posts")),
    path("api/v1/follow/", include("apps.follows.urls", namespace="follows")),
    path("api/v1/blocks", include("apps.blocks.urls", namespace="blocks")),
    path(
        "api/v1/direct-messages/",
        include("apps.directmessages.urls", namespace="directmessages"),
    ),
    path(
        "api/v1/notifications",
        include("apps.notifications.urls", namespace="notifications"),
    ),
    path("api/v1/explore", include("apps.explores.urls", namespace="explores")),
    path("api/v1/supports", include("apps.supports.urls", namespace="supports")),
    path("hello/", hello),
    path("api/v1/websocket-key", WebSocketKey.as_view(), name="websocket_key"),
]

if getattr(settings, "SHOW_SWAGGER", False):

    urlpatterns += [
        path("schema", SpectacularAPIView.as_view(), name="schema"),
        path(
            "swagger",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
