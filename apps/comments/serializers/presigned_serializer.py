from apps.core.storage.s3.constants import COMMENT_ALLOWED_EXTENSIONS
from apps.core.storage.s3.serializers import PresignedUrlRequestSerializer


class CommentPresignedSerializer(PresignedUrlRequestSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_extensions = COMMENT_ALLOWED_EXTENSIONS
