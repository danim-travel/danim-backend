from typing import Any

from rest_framework.permissions import IsAuthenticated

from apps.core.storage.s3 import PresignedUrlView
from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum


class UserProfileImgView(PresignedUrlView):
    permission_classes: list[type[Any]] = [IsAuthenticated]
    action = ActionEnum.UPLOAD
    category = CategoryEnum.USER
    suffix = SuffixEnum.PROFILE
    expires_in: int = 900
