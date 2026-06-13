from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from apps.comments.models import Comment, CommentLike
from apps.core.exceptions.exception import (
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from apps.posts.models import Post


def create_comment(data, user):
    """댓글 생성 및 응답을 위한 img_url 자체 생성 후 응답하는 서비스 로직"""

    post_id = data["post_id"]
    if not Post.objects.filter(id=post_id).exists():
        raise NotFoundException("게시글에 대한 정보를 찾지 못했습니다.")

    content = data.get("content")
    comment_img = data.get("comment_img")

    if comment_img:
        img_key = comment_img.get("key")
        original_img = comment_img.get("original_img")
    else:
        img_key = None
        original_img = None

    new_comment = Comment.objects.create(
        user=user,
        post_id=post_id,
        content=content,
        img_key=img_key,
        original_img=original_img,
    )

    return new_comment


def get_comment_list(post_id, user):
    """응답에 필요한 데이터와 댓글 목록 조회를 위한 서비스 로직"""

    if not Post.objects.filter(id=post_id).exists():
        raise NotFoundException("게시글에 대한 정보를 찾지 못했습니다.")

    query_set = (
        Comment.objects.filter(post_id=post_id)
        .select_related("user")
        .annotate(
            is_liked=(
                Exists(CommentLike.objects.filter(user=user, comment_id=OuterRef("pk")))
                if user.is_authenticated
                else Value(False, output_field=BooleanField())
            ),
            like_count=Count("comment_likes"),
        )
    )
    return query_set


def update_comment(data, user, comment_id):
    """댓글 수정 서비스 로직"""

    target_comment = Comment.objects.filter(id=comment_id).first()
    if not target_comment:
        raise NotFoundException("댓글에 대한 정보를 찾지 못했습니다.")
    if target_comment.user != user:
        raise ForbiddenException("본인이 작성한 댓글만 수정 가능합니다.")

    content = data.get("content", target_comment.content)
    target_comment.content = content

    if data.get("comment_img"):
        img_key = data["comment_img"].get("key", target_comment.img_key)
        original_img = data["comment_img"].get(
            "original_img", target_comment.original_img
        )

        target_comment.img_key = img_key
        target_comment.original_img = original_img

    target_comment.save()

    return target_comment


def delete_comment(comment_id, user):
    """댓글 삭제 서비스 로직"""

    target_comment = Comment.objects.filter(id=comment_id).first()
    if not target_comment:
        raise NotFoundException("댓글에 대한 정보를 찾지 못했습니다.")
    if target_comment.user != user:
        raise ForbiddenException("본인이 작성한 댓글만 삭제 할 수 있습니다.")

    target_comment.delete()


def create_comment_like(comment_id, user):

    if not Comment.objects.filter(id=comment_id).exists():
        raise NotFoundException("해당 댓글을 찾을 수 없습니다.")

    _, is_create = CommentLike.objects.get_or_create(
        user=user,
        comment_id=comment_id,
    )

    if not is_create:
        raise ConflictException("이미 좋아요를 누른 댓글입니다.")

    result = {
        "is_liked": is_create,
        "like_count": CommentLike.objects.filter(comment_id=comment_id).count(),
    }

    return result
