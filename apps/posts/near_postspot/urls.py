from django.urls import URLPattern, path

from apps.posts.near_postspot import views as near_user_views

urlpatterns: list[URLPattern] = [
    path("/user", near_user_views.NearPostSpotUserView.as_view(), name="user"),
]
