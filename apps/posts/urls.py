from django.urls import URLPattern, path

from apps.posts.views import view

app_name = "posts"

urlpatterns: list[URLPattern] = [
    path("", view.PostCreateView.as_view(), name="post_create"),
]
