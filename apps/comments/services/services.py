from django.db.models import BooleanField, Count, Exists, OuterRef, Value

from apps.comments.models import Comment, CommentLike
from apps.core.exceptions.exception import NotFoundException
from apps.core.storage.s3 import s3_svc
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

    if new_comment.img_key is not None:
        new_comment.img_url = s3_svc.create_img_url(img_key)

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
        .order_by("-created_at")
    )
    return query_set


def get_comment_img_url(page):
    """paginate된 댓글 목록 리스트 객체에서 각 겍체에 img_url을 생성하는 서비스 로직"""

    for comment in page:
        if comment.img_key is not None:
            comment.img_url = s3_svc.create_img_url(comment.img_key)
        else:
            comment.img_url = None

    return page
