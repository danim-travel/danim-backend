from django.urls import URLPattern, path

from apps.posts.views import create_view, main_list_view

app_name = "posts"

urlpatterns: list[URLPattern] = [
    path("", create_view.PostCreateView.as_view(), name="post_create"),
    path("/main", main_list_view.PostMainListView.as_view(), name="post_main_list"),
]
