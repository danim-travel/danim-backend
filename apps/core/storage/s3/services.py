from django.conf import settings

from apps.core.utils.ulid import generate_ulid

from .s3_client import s3


class S3Service:
    def __init__(
        self,
        region: str = settings.S3_REGION,
        bucket: str = settings.S3_BUCKET_NAME,
        prefix: str = settings.S3_PREFIX,
        path: str = settings.S3_PATH,
    ) -> None:
        self.region = region
        self.bucket = bucket
        self.prefix = prefix
        self.path = path

    def create_key(self, action: str, category: str, suffix: str | None, extension: str):
        path = self.path.format(
            action=action,
            category=category,
            suffix=suffix,
        )
        return f"{self.prefix}{path}/{generate_ulid()}{extension}"

    def create_img_url(self, key: str):
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def create_upload_presigned_url(
        self, key: str, content_type: str, expires_in: int = 600
    ):
        return s3.generate_presigned_url(
            client_method="put_object",
            params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            expires_in=expires_in,
        )

    def create_download_presigned_url(self, key: str, expires_in: int = 600):
        return s3.generate_presigned_url(
            client_method="get_object",
            params={
                "Bucket": self.bucket,
                "Key": key,
            },
            expires_in=expires_in,
        )

    def delete(self, key: str):
        return s3.delete_object(
            bucket=self.bucket,
            key=key,
        )


s3_svc = S3Service()
