from apps.core.exceptions.exception import NotFoundException
from apps.posts.models import Post


class PostShareService:

    def get_share_url(self, post_id: str, request) -> str:
        """게시글 공유 서비스 로직"""
        try:
            Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        return request.build_absolute_uri(f"/api/v1/posts/{post_id}")
