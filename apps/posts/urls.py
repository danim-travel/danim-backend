from django.urls import path

from apps.posts.views import PostView

app_name = "posts"
urlpatterns = [
    path("", PostView.as_view(), name="post"),
]
