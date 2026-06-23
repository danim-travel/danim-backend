from typing import Any, cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.storage.s3 import ActionEnum, CategoryEnum, SuffixEnum
from apps.core.storage.s3.views import PresignedUrlView
from apps.directmessages.schemas.presigned_url_schema import dm_presigned_url_schema
from apps.directmessages.serializers.presigned_url_serializer import (
    DMPresignedUrlPathSerializer,
)
from apps.directmessages.services.presigned_url_service import get_conversation_for_upload
from apps.users.models import User


class DMPresignedUrlView(PresignedUrlView):
    permission_classes: list[type[Any]] = [IsAuthenticated]
    action = ActionEnum.UPLOAD
    category = CategoryEnum.DM
    suffix = SuffixEnum.NONE
    expires_in: int = 900

    @dm_presigned_url_schema
    def post(self, request: Request, conversation_id: str) -> Response:  # type: ignore[override]
        path = DMPresignedUrlPathSerializer(data={"conversation_id": conversation_id})
        path.is_valid(raise_exception=True)

        get_conversation_for_upload(
            path.validated_data["conversation_id"], cast(User, request.user)
        )

        response = super().post(request)
        response.status_code = status.HTTP_201_CREATED
        return response
