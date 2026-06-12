from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView


def hello(request):
    return JsonResponse({"hello": True})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/users/", include("apps.users.urls", namespace="users")),
    path("api/v1/comments", include("apps.comments.urls", namespace="comments")),
    path("api/v1/posts", include("apps.posts.urls", namespace="posts")),
    path("api/v1/follow/", include("apps.follows.urls", namespace="follows")),
    path(
        "api/v1/direct-messages/",
        include("apps.directmessages.urls", namespace="directmessages"),
    ),
    path("hello/", hello),
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
