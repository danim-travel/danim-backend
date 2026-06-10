from django.urls import URLPattern, path

from apps.posts.views import create_view

app_name = "posts"

urlpatterns: list[URLPattern] = [
    path("", create_view.PostCreateView.as_view(), name="post_create"),
]
