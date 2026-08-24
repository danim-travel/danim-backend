from django.urls import URLPattern, path

from apps.posts.near_postspot import views
from apps.posts.near_postspot import views as near_views

urlpatterns: list[URLPattern] = [
    path("/user", near_views.NearPostSpotUserView.as_view(), name="user"),
    path("/post", near_views.NearPostSpotPostView.as_view(), name="post"),
]
