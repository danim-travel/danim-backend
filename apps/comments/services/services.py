from apps.comments.models import Comment
from apps.core.exceptions.exception import NotFoundException
from apps.core.storage.s3 import s3_svc
from apps.posts.models import Post


def create_comment(data, user):
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
