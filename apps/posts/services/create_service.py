from typing import Any

from django.db import transaction

from apps.posts.models import Post
from apps.posts.services.common import create_spot_with_location_and_images
from apps.users.models import User


class PostCreateService:

    def create_post(self, data: dict[str, Any], user: User) -> Post:
        """게시글 생성 서비스 로직"""

        with transaction.atomic():
            post = Post.objects.create(
                user=user,
                title=data["title"],
                description=data.get("description", ""),
                thumbnail=data.get("thumbnail", ""),
                thumbnail_width=data.get("thumbnail_width"),
                thumbnail_height=data.get("thumbnail_height"),
            )

            for spot_data in data.get("spots", []):
                create_spot_with_location_and_images(post, spot_data)

        return post
