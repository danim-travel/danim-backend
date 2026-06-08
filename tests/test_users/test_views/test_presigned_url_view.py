from datetime import date
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User


class PresignedUrlViewTest(APITestCase):

    user: User

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="testnick",
            name="testname",
            birth_day=date(1999, 1, 1),
            is_active=True,
        )

    def setUp(self) -> None:
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")

        self.s3_patcher = patch("apps.core.storage.s3.views.s3_svc")
        self.mock_s3 = self.s3_patcher.start()
        self.addCleanup(self.s3_patcher.stop)

        self.mock_s3.create_key.return_value = "dev/upload/image/user/profile/uuid.png"
        self.mock_s3.create_img_url.return_value = "https://bucket.s3.region.amazonaws.com/dev/upload/image/user/profile/uuid.png"
        self.mock_s3.create_upload_presigned_url.return_value = (
            "https://bucket.s3.region.amazonaws.com/presigned"
        )

    def test_presigned_url_success(self) -> None:
        """presigned URL 발급 성공"""
        response = self.client.post(
            reverse("users:presigned_url_image"),
            {"original_img": "profile.png"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("presigned_url", response.data)
        self.assertIn("img_url", response.data)
        self.assertIn("key", response.data)

    def test_presigned_url_unauthorized(self) -> None:
        """인증 없이 요청"""
        self.client.credentials()
        response = self.client.post(
            reverse("users:presigned_url_image"),
            {"original_img": "profile.png"},
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_presigned_url_invalid_file_format(self) -> None:
        """유효하지 않은 파일 형식"""
        response = self.client.post(
            reverse("users:presigned_url_image"),
            {"original_img": "profile.gif"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
