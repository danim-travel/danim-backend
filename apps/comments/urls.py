from django.urls import URLPattern, path

from apps.comments.views import CommentView

app_name = "comments"

urlpatterns: list[URLPattern] = [
    path("", CommentView.as_view(), name="Comments"),
]
