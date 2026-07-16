"""S3 attach key 검증 테스트.

presigned 발급은 카테고리를 강제하지만 저장(attach)은 무검증이던 구멍 —
DM으로 받은 이미지 key를 게시글 thumbnail로 심어 공개 재배포하는
교차 카테고리 세탁을 차단하는 계약을 고정한다.
"""

from django.test import TestCase, override_settings

from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import is_valid_attach_key

ULID = "01JZWK7R2MNBX5QD8FHYC3VT9E"  # Crockford Base32 26자

S3_TEST_SETTINGS = {
    "S3_PREFIX": "local/",
    "S3_PATH": "{action}/image/{category}/{suffix}",
}


@override_settings(**S3_TEST_SETTINGS)
class AttachKeyValidatorTest(TestCase):

    # ── 정상 경로 ──────────────────────────────────────────────

    def test_valid_post_key_without_suffix(self):
        key = f"local/upload/image/post/{ULID}.png"
        self.assertTrue(is_valid_attach_key(key, CategoryEnum.POST))

    def test_valid_post_key_with_thumbnail_suffix(self):
        key = f"local/upload/image/post/thumbnail/{ULID}.jpg"
        self.assertTrue(is_valid_attach_key(key, CategoryEnum.POST))

    def test_valid_user_profile_key(self):
        key = f"local/upload/image/user/profile/{ULID}.webp"
        self.assertTrue(is_valid_attach_key(key, CategoryEnum.USER))

    def test_comment_allows_gif(self):
        key = f"local/upload/image/comment/{ULID}.gif"
        self.assertTrue(is_valid_attach_key(key, CategoryEnum.COMMENT))

    # ── 교차 카테고리 차단 (이 검증기의 존재 이유) ──────────────

    def test_rejects_dm_key_attached_as_post(self):
        """DM으로 발급된 key를 게시글에 심는 세탁 경로 차단"""
        dm_key = f"local/upload/image/dm/{ULID}.png"
        self.assertFalse(is_valid_attach_key(dm_key, CategoryEnum.POST))
        self.assertTrue(is_valid_attach_key(dm_key, CategoryEnum.DM))

    def test_rejects_user_profile_key_attached_as_comment(self):
        user_key = f"local/upload/image/user/profile/{ULID}.png"
        self.assertFalse(is_valid_attach_key(user_key, CategoryEnum.COMMENT))

    # ── 형식 위반 차단 ─────────────────────────────────────────

    def test_rejects_gif_for_post(self):
        """gif는 comment 전용 확장자"""
        key = f"local/upload/image/post/{ULID}.gif"
        self.assertFalse(is_valid_attach_key(key, CategoryEnum.POST))

    def test_rejects_non_ulid_tail(self):
        self.assertFalse(
            is_valid_attach_key("local/upload/image/post/evil.png", CategoryEnum.POST)
        )

    def test_rejects_wrong_prefix(self):
        self.assertFalse(
            is_valid_attach_key(f"prod/upload/image/post/{ULID}.png", CategoryEnum.POST)
        )

    def test_rejects_path_traversal_and_nested(self):
        self.assertFalse(
            is_valid_attach_key(
                f"local/upload/image/post/../dm/{ULID}.png", CategoryEnum.POST
            )
        )
        self.assertFalse(
            is_valid_attach_key(
                f"local/upload/image/post/extra/{ULID}.png", CategoryEnum.POST
            )
        )

    def test_rejects_disallowed_extension_and_junk(self):
        self.assertFalse(
            is_valid_attach_key(f"local/upload/image/post/{ULID}.exe", CategoryEnum.POST)
        )
        self.assertFalse(is_valid_attach_key("", CategoryEnum.POST))
        self.assertFalse(is_valid_attach_key(None, CategoryEnum.POST))
        self.assertFalse(is_valid_attach_key("a" * 300, CategoryEnum.POST))


@override_settings(**S3_TEST_SETTINGS)
class AttachKeySerializerIntegrationTest(TestCase):
    """serializer 레벨에서 400으로 거부되는지 — 대표 경로 2곳."""

    def test_post_create_rejects_dm_key_as_thumbnail(self):
        from apps.posts.serializers.create_serializer import PostCreateSerializer

        dm_key = f"local/upload/image/dm/{ULID}.png"
        serializer = PostCreateSerializer(data={"title": "t", "thumbnail": dm_key})
        self.assertFalse(serializer.is_valid())
        self.assertIn("thumbnail", serializer.errors)

    def test_post_create_accepts_own_category_key(self):
        from apps.posts.serializers.create_serializer import PostCreateSerializer

        key = f"local/upload/image/post/thumbnail/{ULID}.png"
        serializer = PostCreateSerializer(data={"title": "t", "thumbnail": key})
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_user_update_rejects_post_key_as_profile(self):
        from apps.users.serializers.me_serializer import UserUpdateRequestSerializer

        post_key = f"local/upload/image/post/{ULID}.png"
        serializer = UserUpdateRequestSerializer(data={"key": post_key})
        self.assertFalse(serializer.is_valid())
        self.assertIn("key", serializer.errors)

    def test_signup_rejects_cross_category_profile_key(self):
        """회원가입 경로가 me 수정의 검증을 우회하지 못한다 (리뷰 지적 회귀 방지)"""
        from apps.users.serializers.signup_serializer import UserSignUpSerializer

        dm_key = f"local/upload/image/dm/{ULID}.png"
        serializer = UserSignUpSerializer(
            data={
                "password": "Password@1",
                "password_confirm": "Password@1",
                "nickname": "nick",
                "name": "name",
                "birth_day": "1995-01-01",
                "email_token": "token",
                "profile_img": dm_key,
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("profile_img", serializer.errors)

    def test_spot_image_rejects_cross_category_key(self):
        """게시글 스팟 이미지 key도 교차 카테고리를 거부한다"""
        from apps.posts.serializers.create_serializer import (
            PostSpotImageCreateSerializer,
        )

        dm_key = f"local/upload/image/dm/{ULID}.png"
        serializer = PostSpotImageCreateSerializer(
            data={"original_img": "a.png", "key": dm_key}
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("key", serializer.errors)
