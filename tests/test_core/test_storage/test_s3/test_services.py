from unittest.mock import patch

from django.test import TestCase

from apps.core.storage.s3.services import ActionEnum, CategoryEnum, S3Service, SuffixEnum

FIXED_ULID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


class CreateKeyTestCase(TestCase):

    def setUp(self):
        self.svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev",
            path="{action}/image/{category}/{suffix}",
        )

    @patch("apps.core.storage.s3.services.generate_ulid", return_value=FIXED_ULID)
    def test_key_structure_with_suffix(self, _):
        # suffix가 있을 때 키가 prefix/action/image/category/suffix/ulid.ext 형태인지 검증
        key = self.svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.POST,
            suffix=SuffixEnum.THUMBNAIL,
            extension=".jpg",
        )
        self.assertEqual(key, f"dev/upload/image/post/thumbnail/{FIXED_ULID}.jpg")

    @patch("apps.core.storage.s3.services.generate_ulid", return_value=FIXED_ULID)
    def test_key_structure_without_suffix(self, _):
        # SuffixEnum.NONE이면 suffix 세그먼트 없이 키가 생성되는지 검증
        key = self.svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.POST,
            suffix=SuffixEnum.NONE,
            extension=".jpg",
        )
        self.assertEqual(key, f"dev/upload/image/post/{FIXED_ULID}.jpg")

    @patch("apps.core.storage.s3.services.generate_ulid", return_value=FIXED_ULID)
    def test_trailing_slash_in_prefix_does_not_produce_double_slash(self, _):
        # prefix 끝에 슬래시가 있어도 //가 생기지 않는지 검증
        svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev/",
            path="{action}/image/{category}/{suffix}",
        )
        key = svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.POST,
            suffix=SuffixEnum.NONE,
            extension=".jpg",
        )
        self.assertFalse(key.startswith("dev//"))

    def test_invalid_action_raises_value_error(self):
        # 잘못된 action 문자열이면 ValueError 발생하는지 검증
        with self.assertRaises(ValueError):
            self.svc.create_key(
                action="invalid",
                category=CategoryEnum.POST,
                suffix=SuffixEnum.NONE,
                extension=".jpg",
            )

    def test_invalid_category_raises_value_error(self):
        # 잘못된 category 문자열이면 ValueError 발생하는지 검증
        with self.assertRaises(ValueError):
            self.svc.create_key(
                action=ActionEnum.UPLOAD,
                category="invalid",
                suffix=SuffixEnum.NONE,
                extension=".jpg",
            )

    def test_invalid_suffix_raises_value_error(self):
        # 잘못된 suffix 문자열이면 ValueError 발생하는지 검증
        with self.assertRaises(ValueError):
            self.svc.create_key(
                action=ActionEnum.UPLOAD,
                category=CategoryEnum.POST,
                suffix="invalid",
                extension=".jpg",
            )


class CreateImgUrlTestCase(TestCase):

    def setUp(self):
        self.svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev",
            path="{action}/image/{category}/{suffix}",
        )

    def test_img_url_format(self):
        # https://{bucket}.s3.{region}.amazonaws.com/{key} 형태인지 검증
        url = self.svc.create_img_url(key="dev/upload/image/post/ulid.jpg")
        self.assertEqual(
            url,
            "https://test-bucket.s3.ap-northeast-2.amazonaws.com/dev/upload/image/post/ulid.jpg",
        )


class CreateUploadPresignedUrlTestCase(TestCase):

    def setUp(self):
        self.svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev",
            path="{action}/image/{category}/{suffix}",
        )

    @patch("apps.core.storage.s3.services.s3")
    def test_delegates_with_put_object(self, mock_s3):
        # client_method="put_object"로 s3에 위임하고 반환값을 패스스루하는지 검증
        mock_s3.generate_presigned_url.return_value = "https://signed.example/upload"

        result = self.svc.create_upload_presigned_url(
            key="dev/upload/image/post/ulid.jpg",
            content_type="image/jpeg",
            expires_in=300,
        )

        self.assertEqual(result, "https://signed.example/upload")
        mock_s3.generate_presigned_url.assert_called_once_with(
            client_method="put_object",
            params={
                "Bucket": "test-bucket",
                "Key": "dev/upload/image/post/ulid.jpg",
                "ContentType": "image/jpeg",
            },
            expires_in=300,
        )

    @patch("apps.core.storage.s3.services.s3")
    def test_default_expires_in_is_900(self, mock_s3):
        # expires_in 미지정 시 900이 넘어가는지 검증
        mock_s3.generate_presigned_url.return_value = "https://signed.example/upload"

        self.svc.create_upload_presigned_url(
            key="dev/upload/image/post/ulid.jpg",
            content_type="image/jpeg",
        )

        _, kwargs = mock_s3.generate_presigned_url.call_args
        self.assertEqual(kwargs["expires_in"], 900)


class CreateDownloadPresignedUrlTestCase(TestCase):

    def setUp(self):
        self.svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev",
            path="{action}/image/{category}/{suffix}",
        )

    @patch("apps.core.storage.s3.services.s3")
    def test_delegates_with_get_object(self, mock_s3):
        # client_method="get_object"로 위임하는지 검증 (put_object와 다른 것이 핵심)
        mock_s3.generate_presigned_url.return_value = "https://signed.example/download"

        result = self.svc.create_download_presigned_url(
            key="dev/upload/image/post/ulid.jpg"
        )

        self.assertEqual(result, "https://signed.example/download")
        mock_s3.generate_presigned_url.assert_called_once_with(
            client_method="get_object",
            params={
                "Bucket": "test-bucket",
                "Key": "dev/upload/image/post/ulid.jpg",
            },
            expires_in=900,
        )


class DeleteTestCase(TestCase):

    def setUp(self):
        self.svc = S3Service(
            region="ap-northeast-2",
            bucket="test-bucket",
            prefix="dev",
            path="{action}/image/{category}/{suffix}",
        )

    @patch("apps.core.storage.s3.services.s3")
    def test_delegates_to_delete_object(self, mock_s3):
        # bucket과 key를 올바르게 넘기는지 검증
        self.svc.delete(key="dev/upload/image/post/ulid.jpg")

        mock_s3.delete_object.assert_called_once_with(
            bucket="test-bucket",
            key="dev/upload/image/post/ulid.jpg",
        )

    @patch("apps.core.storage.s3.services.s3")
    def test_returns_none(self, mock_s3):
        # None을 반환하는지 검증
        result = self.svc.delete(key="dev/upload/image/post/ulid.jpg")
        self.assertIsNone(result)
