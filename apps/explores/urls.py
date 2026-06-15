from django.urls import URLPattern, path

from apps.explores.views import ExploresView

app_name = "explores"

urlpatterns: list[URLPattern] = [
    path("", ExploresView.as_view(), name="explores"),
]
