from apps.core.exceptions.exception import ConflictException, NotFoundException
from apps.posts.models import Post
from apps.posts.models.bookmark_model import BookMark
from apps.users.models import User


class BookmarkService:

    def create_bookmark(self, post_id: str, request_user: User):
        if not Post.objects.filter(id=post_id).exists():
            raise NotFoundException("해당 게시글을 찾을 수 없습니다.")
        bookmark, created = BookMark.objects.get_or_create(
            post_id=post_id,
            user=request_user,
        )
        if not created:
            raise ConflictException("이미 북마크한 게시글입니다.")

        return bookmark

    def delete_bookmark(self, post_id: str, request_user: User):
        if not Post.objects.filter(id=post_id).exists():
            raise NotFoundException("해당 게시글을 찾을 수 없습니다.")
        BookMark.objects.filter(
            post_id=post_id,
            user=request_user,
        ).delete()
