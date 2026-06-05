from enum import StrEnum

from django.conf import settings

from apps.core.utils.ulid import generate_ulid

from .s3_client import s3


class ActionEnum(StrEnum):
    UPLOAD = "upload"


class CategoryEnum(StrEnum):
    POST = "post"
    USER = "user"
    COMMENT = "comment"


class SuffixEnum(StrEnum):
    NONE = ""
    PROFILE = "profile"
    THUMBNAIL = "thumbnail"


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

    def create_key(self, action: str, category: str, suffix: str, extension: str) -> str:
        _validate_key_values(action, category, suffix)

        path = self.path.format(
            action=action,
            category=category,
            suffix=suffix,
        )
        return (
            f"{self.prefix.rstrip("/")}/{path.rstrip("/")}/{generate_ulid()}{extension}"
        )

    def create_img_url(self, key: str) -> str:
        return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

    def create_upload_presigned_url(
        self, key: str, content_type: str, expires_in: int = 900
    ) -> str:
        return s3.generate_presigned_url(
            client_method="put_object",
            params={
                "Bucket": self.bucket,
                "Key": key,
                "ContentType": content_type,
            },
            expires_in=expires_in,
        )

    def create_download_presigned_url(self, key: str, expires_in: int = 900) -> str:
        return s3.generate_presigned_url(
            client_method="get_object",
            params={
                "Bucket": self.bucket,
                "Key": key,
            },
            expires_in=expires_in,
        )

    def delete(self, key: str) -> None:
        s3.delete_object(
            bucket=self.bucket,
            key=key,
        )


def _validate_key_values(action: str, category: str, suffix: str) -> None:
    if action not in ActionEnum:
        raise ValueError(f"허용되지 않은 action: {action}")
    if category not in CategoryEnum:
        raise ValueError(f"허용되지 않은 category: {category}")
    if suffix is not None and suffix not in SuffixEnum:
        raise ValueError(f"허용되지 않은 suffix: {suffix}")


s3_svc = S3Service()
