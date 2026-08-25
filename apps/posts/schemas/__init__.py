from apps.posts.schemas.bookmark_list_view_schema import bookmark_list_schema
from apps.posts.schemas.bookmark_view_schema import (
    bookmark_create_schema,
    bookmark_delete_schema,
)
from apps.posts.schemas.create_view_schema import post_create_schema
from apps.posts.schemas.delete_view_schema import post_delete_schema
from apps.posts.schemas.detail_view_schema import post_detail_schema
from apps.posts.schemas.like_view_schema import post_like_schema, post_unlike_schema
from apps.posts.schemas.main_list_view_schema import post_main_list_schema
from apps.posts.schemas.presigned_url_schemas import post_presigned_schema
from apps.posts.schemas.share_view_schema import post_share_schema
from apps.posts.schemas.update_view_schema import post_update_schema

__all__ = [
    "bookmark_create_schema",
    "bookmark_delete_schema",
    "bookmark_list_schema",
    "post_create_schema",
    "post_delete_schema",
    "post_detail_schema",
    "post_like_schema",
    "post_main_list_schema",
    "post_presigned_schema",
    "post_share_schema",
    "post_unlike_schema",
    "post_update_schema",
]
