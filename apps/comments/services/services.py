from django.db import transaction
from django.db.models import BooleanField, Exists, F, OuterRef, Value

from apps.blocks.services import is_blocked_between
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
    # exists() 대신 작성자 id를 함께 조회 (쿼리 수 동일) — 차단 게이트에 사용
    post_author_id = (
        Post.objects.filter(id=post_id).values_list("user_id", flat=True).first()
    )
    if post_author_id is None:
        raise NotFoundException("게시글에 대한 정보를 찾지 못했습니다.")
    if is_blocked_between(user.id, post_author_id):
        raise ForbiddenException("차단 관계의 게시글에는 댓글을 작성할 수 없습니다.")

    content = data.get("content")
    comment_img = data.get("comment_img")

    if comment_img:
        img_key = comment_img.get("key")
        original_img = comment_img.get("original_img")
    else:
        img_key = None
        original_img = None

    with transaction.atomic():
        new_comment = Comment.objects.create(
            user=user,
            post_id=post_id,
            content=content,
            img_key=img_key,
            original_img=original_img,
        )
        Post.objects.filter(id=post_id).update(comment_count=F("comment_count") + 1)

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
            )
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

    with transaction.atomic():
        # 삭제된 행이 있을 때만 카운터를 감소시킨다.
        # 소유권 확인(위 조회)과 삭제 사이에 다른 요청이 먼저 지운 경우(더블탭·재시도)
        # 무조건 -1을 실행하면 comment_count가 실제 댓글 수보다 작아지고,
        # 0에 도달하면 PositiveIntegerField의 DB CHECK 위반으로
        # 남은 댓글의 삭제가 전부 500으로 막힌다.
        deleted, _ = Comment.objects.filter(id=target_comment.id).delete()
        if not deleted:
            raise NotFoundException("댓글에 대한 정보를 찾지 못했습니다.")
        Post.objects.filter(id=target_comment.post_id).update(
            comment_count=F("comment_count") - 1
        )


def create_comment_like(comment_id, user):

    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        raise NotFoundException("해당 댓글을 찾을 수 없습니다.")

    with transaction.atomic():
        _, is_create = CommentLike.objects.get_or_create(
            user=user,
            comment_id=comment_id,
        )

        if not is_create:
            raise ConflictException("이미 좋아요를 누른 댓글입니다.")
        Comment.objects.filter(id=comment.id).update(like_count=F("like_count") + 1)

    result = {
        "is_liked": is_create,
        "like_count": comment.like_count + 1,
    }

    return result


def delete_comment_like(comment_id, user):

    comment = Comment.objects.filter(id=comment_id).first()
    if not comment:
        raise NotFoundException("해당 댓글을 찾을 수 없습니다.")

    with transaction.atomic():
        deleted_count, _ = CommentLike.objects.filter(comment=comment, user=user).delete()

        if deleted_count == 0:
            raise NotFoundException("좋아요를 누르지 않은 댓글입니다.")

        Comment.objects.filter(id=comment.id).update(like_count=F("like_count") - 1)

    result = {
        "is_liked": False,
        "like_count": comment.like_count - 1,
    }
    return result
