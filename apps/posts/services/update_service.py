from typing import Any

from django.db import transaction

from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from apps.posts.models import Post
from apps.posts.services.common import create_spot_with_location_and_images
from apps.users.models import User


class PostUpdateService:

    def update_post(self, post_id: str, data: dict[str, Any], user: User) -> None:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        if post.user_id != user.id:
            raise ForbiddenException("본인의 게시글만 수정할 수 있습니다.")

        with transaction.atomic():
            if "title" in data:
                post.title = data["title"]
            if "description" in data:
                post.description = data["description"]
            if "thumbnail" in data:
                post.thumbnail = data["thumbnail"]
            post.save()

            if "spots" in data:
                post.spots.all().delete()
                for spot_data in data["spots"]:
                    create_spot_with_location_and_images(post, spot_data)
