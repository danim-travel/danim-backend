from typing import Any

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)
from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc


class PresignedUrlView(APIView):
    """
    원본 파일명을 받아서 key, img_url, presigned_url을 응답하는 뷰
    사용법은 apps/core/storage/s3/__init__.py 참고
    """

    permission_classes: list[type[Any]] = []

    action: ActionEnum
    category: CategoryEnum
    suffix: SuffixEnum
    expires_in: int = 900

    def post(self, request: Request) -> Response:
        req = PresignedUrlRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        key = s3_svc.create_key(
            action=self.action,
            category=self.category,
            suffix=self.suffix,
            extension=req.validated_data["extension"],
        )

        img_url = s3_svc.create_img_url(key=key)

        presigned_url = s3_svc.create_upload_presigned_url(
            key=key,
            content_type=req.validated_data["content_type"],
            expires_in=self.expires_in,
        )

        res = PresignedUrlResponseSerializer(
            {"key": key, "img_url": img_url, "presigned_url": presigned_url}
        )

        return Response(res.data, status=status.HTTP_200_OK)
