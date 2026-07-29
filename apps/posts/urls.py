from django.urls import URLPattern, URLResolver, include, path

from apps.posts.views import (
    bookmark_list_view,
    bookmark_view,
    like_view,
    post_view,
    presigned_url_post_view,
    share_view,
)

app_name = "posts"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", post_view.PostListCreateView.as_view(), name="post_list_create"),
    path("/main", post_view.PostListCreateView.as_view(), name="post_main_list"),
    path(
        "/presigned-url",
        presigned_url_post_view.PostImageView.as_view(),
        name="presigned_url_post",
    ),
    path(
        "/bookmarks", bookmark_list_view.BookmarkListView.as_view(), name="bookmark_list"
    ),
    path("/nearspots", include("apps.posts.near_postspot.urls")),
    path("/<str:post_id>", post_view.PostDetailView.as_view(), name="post_detail"),
    path("/<str:post_id>/like", like_view.PostLikeView.as_view(), name="post_like"),
    path(
        "/<str:post_id>/bookmark", bookmark_view.BookmarkView.as_view(), name="bookmark"
    ),
    path("/<str:post_id>/share", share_view.PostShareView.as_view(), name="post_share"),
]
