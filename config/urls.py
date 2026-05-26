from django.conf import settings
from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def hello(request):
    return JsonResponse({"hello": True})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello", hello),
]

if settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("schema", SpectacularAPIView.as_view(), name="schema"),
        path(
            "swagger",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
