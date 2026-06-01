from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.urls import path, reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum
from apps.core.storage.s3.views import PresignedUrlView


class ConcretePresignedUrlView(PresignedUrlView):
    # 추상 클래스인 PresignedUrlView를 직접 테스트하기 위한 구체 클래스
    action = ActionEnum.UPLOAD
    category = CategoryEnum.POST
    suffix = SuffixEnum.THUMBNAIL
    expires_in = 900


urlpatterns = [
    path(
        "test/presigned-url/",
        ConcretePresignedUrlView.as_view(),
        name="test-presigned-url",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
@patch("apps.core.storage.s3.views.s3_svc")
class PresignedUrlViewTestCase(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = "/test/presigned-url/"

    def test_post_returns_200_with_valid_data(self, mock_s3_svc):
        # 유효한 파일명 요청 시 200과 key/img_url/presigned_url 응답하는지 검증
        mock_s3_svc.create_key.return_value = "dev/upload/image/post/thumbnail/ulid.jpg"
        mock_s3_svc.create_img_url.return_value = (
            "https://bucket.s3.amazonaws.com/dev/upload/image/post/thumbnail/ulid.jpg"
        )
        mock_s3_svc.create_upload_presigned_url.return_value = (
            "https://signed.example/upload"
        )

        response = self.client.post(
            self.url,
            data={"original_img": "photo.jpg"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["key"], "dev/upload/image/post/thumbnail/ulid.jpg")
        self.assertEqual(
            response.data["img_url"],
            "https://bucket.s3.amazonaws.com/dev/upload/image/post/thumbnail/ulid.jpg",
        )
        self.assertEqual(response.data["presigned_url"], "https://signed.example/upload")

    def test_s3_svc_called_with_correct_args(self, mock_s3_svc):
        # s3_svc의 각 메서드가 올바른 인자로 호출되는지 검증
        mock_s3_svc.create_key.return_value = "dev/upload/image/post/thumbnail/ulid.jpg"
        mock_s3_svc.create_img_url.return_value = "https://bucket.s3.amazonaws.com/key"
        mock_s3_svc.create_upload_presigned_url.return_value = (
            "https://signed.example/upload"
        )

        self.client.post(self.url, data={"original_img": "photo.jpg"}, format="json")

        mock_s3_svc.create_key.assert_called_once_with(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.POST,
            suffix=SuffixEnum.THUMBNAIL,
            extension=".jpg",
        )
        mock_s3_svc.create_img_url.assert_called_once_with(
            key="dev/upload/image/post/thumbnail/ulid.jpg",
        )
        mock_s3_svc.create_upload_presigned_url.assert_called_once_with(
            key="dev/upload/image/post/thumbnail/ulid.jpg",
            content_type="image/jpeg",
            expires_in=900,
        )

    def test_post_returns_400_with_invalid_extension(self, mock_s3_svc):
        # 허용되지 않은 확장자 요청 시 400 응답하는지 검증
        response = self.client.post(
            self.url,
            data={"original_img": "photo.gif"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_s3_svc.create_key.assert_not_called()

    def test_post_returns_400_with_missing_field(self, mock_s3_svc):
        # original_img 필드 누락 시 400 응답하는지 검증
        response = self.client.post(self.url, data={}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        mock_s3_svc.create_key.assert_not_called()
