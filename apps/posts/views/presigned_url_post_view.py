from typing import Any

from rest_framework.permissions import IsAuthenticated

from apps.core.storage.s3 import ActionEnum, CategoryEnum, SuffixEnum
from apps.core.storage.s3.views import PresignedUrlView
from apps.posts.schemas.presigned_url_schemas import post_presigned_schema


@post_presigned_schema
class PostImageView(PresignedUrlView):
    permission_classes: list[type[Any]] = [IsAuthenticated]
    action = ActionEnum.UPLOAD
    category = CategoryEnum.POST
    suffix = SuffixEnum.NONE
    expires_in = 900
