from django.urls import URLPattern, URLResolver, include, path

from apps.posts.views import (
    bookmark_list_view,
    bookmark_view,
    create_view,
    detail_view,
    like_view,
    main_list_view,
    presigned_url_post_view,
    share_view,
)

app_name = "posts"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", create_view.PostCreateView.as_view(), name="post_create"),
    path("/main", main_list_view.PostMainListView.as_view(), name="post_main_list"),
    path(
        "/presigned-url",
        presigned_url_post_view.PostImageView.as_view(),
        name="presigned_url_post",
    ),
    path(
        "/bookmarks", bookmark_list_view.BookmarkListView.as_view(), name="bookmark_list"
    ),
    path("/<str:post_id>", detail_view.PostDetailView.as_view(), name="post_detail"),
    path("/<str:post_id>/like", like_view.PostLikeView.as_view(), name="post_like"),
    path(
        "/<str:post_id>/bookmark", bookmark_view.BookmarkView.as_view(), name="bookmark"
    ),
    path("/<str:post_id>/share", share_view.PostShareView.as_view(), name="post_share"),
    path("/nearspots", include("apps.posts.near_postspot.urls")),
]
