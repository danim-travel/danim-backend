from unittest.mock import MagicMock, call, patch

from botocore.config import Config
from django.test import TestCase

from apps.core.storage.s3.s3_client import S3Client


class S3ClientInitTestCase(TestCase):
    @patch("apps.core.storage.s3.s3_client.boto3.client")
    def test_passes_credentials_and_config_to_boto3(self, mock_factory):
        config = Config(s3={"addressing_style": "virtual"})

        S3Client(
            config=config,
            region_name="ap-northeast-2",
            aws_access_key_id="AKIA_TEST",
            aws_secret_access_key="SECRET_TEST",
        )

        mock_factory.assert_called_once_with(
            "s3",
            config=config,
            region_name="ap-northeast-2",
            aws_access_key_id="AKIA_TEST",
            aws_secret_access_key="SECRET_TEST",
        )


class GeneratePresignedUrlTestCase(TestCase):
    @patch("apps.core.storage.s3.s3_client.boto3.client")
    def test_delegates_with_pascal_case_kwargs(self, mock_factory):
        inner = MagicMock()
        mock_factory.return_value = inner
        inner.generate_presigned_url.return_value = "https://signed.example/url"

        client = S3Client()
        params = {"Bucket": "b", "Key": "k", "ContentType": "image/png"}
        result = client.generate_presigned_url(
            client_method="put_object",
            params=params,
            expires_in=300,
        )

        self.assertEqual(result, "https://signed.example/url")
        inner.generate_presigned_url.assert_called_once_with(
            ClientMethod="put_object",
            Params=params,
            ExpiresIn=300,
        )

    @patch("apps.core.storage.s3.s3_client.boto3.client")
    def test_default_expires_in_is_900(self, mock_factory):
        inner = MagicMock()
        mock_factory.return_value = inner

        client = S3Client()
        client.generate_presigned_url(
            client_method="get_object",
            params={"Bucket": "b", "Key": "k"},
        )

        _, kwargs = inner.generate_presigned_url.call_args
        self.assertEqual(kwargs["ExpiresIn"], 900)


class DeleteObjectTestCase(TestCase):
    @patch("apps.core.storage.s3.s3_client.boto3.client")
    def test_delegates_with_pascal_case_kwargs(self, mock_factory):
        inner = MagicMock()
        mock_factory.return_value = inner
        inner.delete_object.return_value = {"ResponseMetadata": {"HTTPStatusCode": 204}}

        client = S3Client()
        result = client.delete_object(bucket="my-bucket", key="path/to/obj.jpg")

        self.assertEqual(result, {"ResponseMetadata": {"HTTPStatusCode": 204}})
        inner.delete_object.assert_called_once_with(
            Bucket="my-bucket",
            Key="path/to/obj.jpg",
        )
