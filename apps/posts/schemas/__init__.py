from apps.posts.schemas.create_view_schema import post_create_schema
from apps.posts.schemas.delete_view_schema import post_delete_schema
from apps.posts.schemas.detail_view_schema import post_detail_schema
from apps.posts.schemas.main_list_view_schema import post_main_list_schema
from apps.posts.schemas.update_view_schema import post_update_schema

__all__ = [
    "post_create_schema",
    "post_delete_schema",
    "post_detail_schema",
    "post_main_list_schema",
    "post_update_schema",
]
