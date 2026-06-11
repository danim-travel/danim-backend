from django.urls import URLPattern, path

from apps.posts.views import (
    create_view,
    detail_view,
    main_list_view,
    presigned_url_post_view,
)

app_name = "posts"

urlpatterns: list[URLPattern] = [
    path("", create_view.PostCreateView.as_view(), name="post_create"),
    path("/main", main_list_view.PostMainListView.as_view(), name="post_main_list"),
    path(
        "/presigned-url",
        presigned_url_post_view.PostImageView.as_view(),
        name="presigned_url_post",
    ),
    path("/<str:post_id>", detail_view.PostDetailView.as_view(), name="post_detail"),
]
