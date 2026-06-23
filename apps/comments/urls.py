from django.urls import URLPattern, path

from apps.comments.views import (
    CommentDetailView,
    CommentLikeView,
    CommentPresignedURLView,
    CommentView,
)

app_name = "comments"

urlpatterns: list[URLPattern] = [
    path("", CommentView.as_view(), name="Comments"),
    path("/presigned-url", CommentPresignedURLView.as_view(), name="PresignedUrl"),
    path("/<str:comment_id>", CommentDetailView.as_view(), name="CommentDetail"),
    path("/<str:comment_id>/like", CommentLikeView.as_view(), name="CommentLike"),
]
