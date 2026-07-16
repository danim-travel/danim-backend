from django.urls import URLPattern, path

from apps.blocks.views import BlockListView, BlockView

app_name = "blocks"

urlpatterns: list[URLPattern] = [
    path("", BlockListView.as_view(), name="block_list"),
    path("/<str:user_id>", BlockView.as_view(), name="block"),
]
