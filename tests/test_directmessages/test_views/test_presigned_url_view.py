from unittest.mock import patch

from django.utils import timezone

from tests.test_core.bases.conversation_base import ConversationBaseTest

FIXED_KEY = "dev/upload/image/dm/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg"
FIXED_IMG_URL = (
    "https://bucket.s3.amazonaws.com/dev/upload/image/dm/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg"
)
FIXED_PRESIGNED_URL = "https://signed.example/upload"


@patch("apps.core.storage.s3.views.s3_svc")
class TestDMPresignedUrlView(ConversationBaseTest):

    def setUp(self):
        super().setUp()
        self.url = f"/api/v1/direct-messages/conversations/{self.conversation.id}/messages/presigned-url"

    def test_user1_returns_201(self, mock_s3_svc):
        """user1 정상 요청 시 201과 key/img_url/presigned_url 반환"""
        mock_s3_svc.create_key.return_value = FIXED_KEY
        mock_s3_svc.create_img_url.return_value = FIXED_IMG_URL
        mock_s3_svc.create_upload_presigned_url.return_value = FIXED_PRESIGNED_URL

        self.client.force_authenticate(user=self.conversation.user1)
        response = self.client.post(
            self.url, data={"original_img": "photo.jpg"}, format="json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["key"], FIXED_KEY)
        self.assertEqual(response.data["img_url"], FIXED_IMG_URL)
        self.assertEqual(response.data["presigned_url"], FIXED_PRESIGNED_URL)

    def test_user2_returns_201(self, mock_s3_svc):
        """user2 정상 요청 시 201 반환"""
        mock_s3_svc.create_key.return_value = FIXED_KEY
        mock_s3_svc.create_img_url.return_value = FIXED_IMG_URL
        mock_s3_svc.create_upload_presigned_url.return_value = FIXED_PRESIGNED_URL

        self.client.force_authenticate(user=self.conversation.user2)
        response = self.client.post(
            self.url, data={"original_img": "photo.jpg"}, format="json"
        )

        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_returns_401(self, mock_s3_svc):
        """비로그인 요청 시 401 반환"""
        response = self.client.post(
            self.url, data={"original_img": "photo.jpg"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_non_participant_returns_404(self, mock_s3_svc):
        """대화 참여자가 아닌 유저 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.post(
            self.url, data={"original_img": "photo.jpg"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_already_left_returns_404(self, mock_s3_svc):
        """대화방 나간 유저 요청 시 404 반환"""
        self.conversation.user1_left_at = timezone.now()
        self.conversation.save()

        self.client.force_authenticate(user=self.conversation.user1)
        response = self.client.post(
            self.url, data={"original_img": "photo.jpg"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_extension_returns_400(self, mock_s3_svc):
        """허용되지 않은 확장자 요청 시 400 반환"""
        self.client.force_authenticate(user=self.conversation.user1)
        response = self.client.post(
            self.url, data={"original_img": "photo.gif"}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        mock_s3_svc.create_key.assert_not_called()

    def test_missing_original_img_returns_400(self, mock_s3_svc):
        """original_img 누락 시 400 반환"""
        self.client.force_authenticate(user=self.conversation.user1)
        response = self.client.post(self.url, data={}, format="json")
        self.assertEqual(response.status_code, 400)
        mock_s3_svc.create_key.assert_not_called()

    def test_short_conversation_id_returns_404(self, mock_s3_svc):
        """26자 미만 conversation_id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(
            "/api/v1/direct-messages/conversations/tooshort/messages/presigned-url",
            data={"original_img": "photo.jpg"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_long_conversation_id_returns_404(self, mock_s3_svc):
        """26자 초과 conversation_id 요청 시 404 반환"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.post(
            "/api/v1/direct-messages/conversations/toolongid000000000000000000/messages/presigned-url",
            data={"original_img": "photo.jpg"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
