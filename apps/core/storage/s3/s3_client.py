import boto3
from botocore.config import Config
from django.conf import settings
from mypy_boto3_s3.type_defs import DeleteObjectOutputTypeDef


class S3Client:
    """boto3 기능 중 s3에 연결"""

    def __init__(
        self,
        config: Config = settings.S3_CONFIG,
        region_name: str = settings.S3_REGION,
        aws_access_key_id: str = settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key: str = settings.S3_SECRET_ACCESS_KEY,
    ) -> None:

        self._s3 = boto3.client(
            "s3",
            config=config,
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
        )

    # boto3의 generate_presigned_url를 래핑
    def generate_presigned_url(
        self, client_method: str, params: dict, expires_in: int = 900
    ) -> str:
        return self._s3.generate_presigned_url(
            ClientMethod=client_method,
            Params=params,
            ExpiresIn=expires_in,
        )

    # boto3의 delete_object를 래핑
    def delete_object(self, bucket: str, key: str) -> DeleteObjectOutputTypeDef:
        return self._s3.delete_object(Bucket=bucket, Key=key)


s3 = S3Client()
