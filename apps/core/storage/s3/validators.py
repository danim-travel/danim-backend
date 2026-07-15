"""클라이언트가 첨부(attach)하는 S3 key 검증.

presigned 발급(`S3Service.create_key`)은 카테고리를 강제하지만, 발급된 key를
게시글·댓글·프로필·DM에 **저장하는 쪽은 지금까지 무검증**이었다. presigned GET
URL 경로에는 key가 그대로 노출되므로, 검증이 없으면 DM으로 받은 이미지의 key를
자기 게시글 thumbnail로 저장해 **비공개 문맥의 객체를 공개 재배포**하는
교차 카테고리 세탁이 가능하다.

여기서는 `create_key`가 발급하는 형식(S3_PREFIX / S3_PATH 템플릿 / ULID /
허용 확장자)과 **카테고리 일치**까지 검증한다. 발급자-소유자 바인딩
(발급 key를 기록해 대조)은 후속 과제로 남긴다.
"""

import re

from django.conf import settings
from rest_framework import serializers

from apps.core.storage.s3.constants import (
    ALLOWED_EXTENSIONS,
    COMMENT_ALLOWED_EXTENSIONS,
)
from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum

# python-ulid str(): Crockford Base32 대문자 26자
_ULID_PATTERN = r"[0-9A-HJKMNP-TV-Z]{26}"
# PresignedUrlResponseSerializer.key 의 max_length 와 동일 상한
_MAX_KEY_LENGTH = 255


def _extensions_for(category: str) -> dict[str, str]:
    """카테고리별 허용 확장자 (댓글만 gif 추가 허용)."""
    if category == CategoryEnum.COMMENT:
        return COMMENT_ALLOWED_EXTENSIONS
    return ALLOWED_EXTENSIONS


def _allowed_dirs(category: str) -> list[str]:
    """create_key와 동일한 규칙으로, 이 카테고리에 발급될 수 있는 디렉토리 목록.

    settings.S3_PATH 템플릿을 그대로 사용하므로 경로 규칙이 바뀌어도
    발급 측(create_key)과 검증 측이 함께 움직인다.
    """
    prefix = settings.S3_PREFIX.rstrip("/")
    dirs = []
    for suffix in SuffixEnum:
        path = settings.S3_PATH.format(
            action=ActionEnum.UPLOAD, category=category, suffix=suffix
        )
        dirs.append(f"{prefix}/{path.rstrip('/')}/")
    return dirs


def is_valid_attach_key(key: object, category: str) -> bool:
    """key가 해당 카테고리용으로 발급된 형식인지 검증한다."""
    if not isinstance(key, str) or not key or len(key) > _MAX_KEY_LENGTH:
        return False

    ext_pattern = "|".join(re.escape(e.lstrip(".")) for e in _extensions_for(category))
    tail_re = re.compile(rf"{_ULID_PATTERN}\.(?:{ext_pattern})\Z")
    return any(
        key.startswith(allowed_dir) and tail_re.fullmatch(key[len(allowed_dir) :])
        for allowed_dir in _allowed_dirs(category)
    )


def validate_attach_key(key: str, category: str) -> str:
    """DRF serializer 필드 검증용. 형식이 어긋나면 ValidationError(400)."""
    if not is_valid_attach_key(key, category):
        raise serializers.ValidationError("유효하지 않은 이미지 key입니다.")
    return key
