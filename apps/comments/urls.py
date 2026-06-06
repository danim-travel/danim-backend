from django.urls import URLPattern, path

from apps.comments.views import CommentDetailView, CommentPresignedURLView, CommentView

app_name = "comments"

urlpatterns: list[URLPattern] = [
    path("", CommentView.as_view(), name="Comments"),
    path("/presigned_url", CommentPresignedURLView.as_view(), name="PresignedUrl"),
    path("/<str:comment_id>", CommentDetailView.as_view(), name="CommentDetail"),
]
