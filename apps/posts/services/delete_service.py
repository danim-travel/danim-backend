from apps.core.exceptions.exception import ForbiddenException, NotFoundException
from apps.posts.models import Post
from apps.users.models import User


class PostDeleteService:

    def delete_post(self, post_id: str, user: User) -> None:
        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFoundException("게시글을 찾을 수 없습니다.")

        if post.user_id != user.id:
            raise ForbiddenException("본인의 게시글만 삭제할 수 있습니다.")

        post.delete()
