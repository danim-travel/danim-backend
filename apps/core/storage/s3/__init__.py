from apps.core.storage.s3.views import PresignedUrlView

"""
사용법:

from apps.core.storage.s3 import PresignedUrlView, ActionEnum, CategoryEnum, SuffixEnum

class ExampleView(PresignedUrlView):
    permission_classes: list[type[Any]] = []
    action: ActionEnum  # ActionEnum.UPLOAD, ActionEnum.DOWNLOAD
    category: CategoryEnum  # CategoryEnum.POST, CategoryEnum.USER, CategoryEnum.COMMENT
    suffix: SuffixEnum  # SuffixEnum.NONE, SuffixEnum.PROFILE, SuffixEnum.THUMBNAIL
    expires_in: int = 900

key 구조: {prefix}{action}/image/{category}/{suffix}/ulid.jpg
       ex)  dev/upload/image/post/thumbnail/ulid.jpg
            dev/upload/image/post/ulid.jpg
"""


from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc

"""
사용법:


from apps.core.storage.s3 import s3_svc

1. key 생성: s3_svc.create_key(args)
2. img_url 생성: s3_svc.create_img_url(args)
3. 업로드용 presigned_url 생성: s3_svc.create_upload_presigned_url(args)
4. 다운로드용 presigned_url 생성: s3_svc.create_download_presigned_url(args)
5. s3 파일 삭제: s3_svc.delete(key)
"""

__all__ = ["s3_svc", "PresignedUrlView", "ActionEnum", "CategoryEnum", "SuffixEnum"]
