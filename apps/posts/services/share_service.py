from django.conf import settings

from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post


class PostShareService:

    def get_share_url(self, post_id: str) -> str:
        """게시글 공유 서비스 로직"""
        try:
            Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        return f"{settings.FRONTEND_URL}/posts/{post_id}"
