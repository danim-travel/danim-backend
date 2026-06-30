from apps.core.storage.s3.constants import COMMENT_ALLOWED_EXTENSIONS
from apps.core.storage.s3.serializers import PresignedUrlRequestSerializer


class CommentPresignedSerializer(PresignedUrlRequestSerializer):
    """댓글 presigned URL 요청 serializer. gif를 포함한 확장자를 허용한다."""

    allowed_extensions: dict[str, str] = COMMENT_ALLOWED_EXTENSIONS
