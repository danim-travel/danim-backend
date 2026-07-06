from unittest.mock import patch

from apps.users.models import User
from apps.users.serializers.user_search_serializer import UserSearchResponseSerializer
from tests.test_core.bases.user_base import UserBase


class UserSearchSerializerTest(UserBase):
    user: User

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    @patch("apps.users.models.models.s3_svc.create_download_presigned_url")
    def test_search_users_serializer(self, mock_presigned) -> None:
        mock_presigned.return_value = (
            "https://bucket.s3.amazonaws.com/test_key?X-Amz-Signature=abc123"
        )
        serializer = UserSearchResponseSerializer(self.user1)
        data = serializer.data

        self.assertEqual(data["user_id"], self.user1.id)
        self.assertEqual(data["nickname"], self.user1.nickname)
        assert self.user1.profile_img is not None
        self.assertIn("test_key", data["profile_img"])
        self.assertIn("X-Amz-Signature", data["profile_img"])
        mock_presigned.assert_called_once_with(self.user1.profile_img)
