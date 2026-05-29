from django.test import TestCase

from apps.core.exceptions.exception import ValidationException
from apps.core.storage.s3.serializers import (
    PresignedUrlRequestSerializer,
    PresignedUrlResponseSerializer,
)


class PresignedUrlRequestSerializerTestCase(TestCase):

    def test_valid_extension_passes(self):
        s = PresignedUrlRequestSerializer(data={"original_img": "photo.jpg"})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data["extension"], ".jpg")
        self.assertEqual(s.validated_data["content_type"], "image/jpeg")

    def test_extension_is_lowercased(self):
        s = PresignedUrlRequestSerializer(data={"original_img": "photo.JPG"})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.validated_data["extension"], ".jpg")

    def test_invalid_extension_raises(self):
        s = PresignedUrlRequestSerializer(data={"original_img": "photo.gif"})
        with self.assertRaises(ValidationException):
            s.is_valid(raise_exception=True)

    def test_no_extension_raises(self):
        s = PresignedUrlRequestSerializer(data={"original_img": "photo"})
        with self.assertRaises(ValidationException):
            s.is_valid(raise_exception=True)

    def test_original_img_too_long_raises(self):
        s = PresignedUrlRequestSerializer(
            data={"original_img": "a" * 97 + ".jpg"}
        )  # 101자
        self.assertFalse(s.is_valid())

    def test_missing_field_raises(self):
        s = PresignedUrlRequestSerializer(data={})
        self.assertFalse(s.is_valid())


class PresignedUrlResponseSerializerTestCase(TestCase):

    def _valid_data(self):
        return {
            "key": "dev/upload/image/post/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg",
            "img_url": "https://bucket.s3.ap-northeast-2.amazonaws.com/dev/upload/image/post/01ARZ3NDEKTSV4RRFFQ69G5FAV.jpg",
            "presigned_url": "https://bucket.s3.amazonaws.com/signed?X-Amz-Signature=abc",
        }

    def test_valid_data_serializes(self):
        s = PresignedUrlResponseSerializer(data=self._valid_data())
        self.assertTrue(s.is_valid())

    def test_missing_key_raises(self):
        data = self._valid_data()
        del data["key"]
        s = PresignedUrlResponseSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_missing_img_url_raises(self):
        data = self._valid_data()
        del data["img_url"]
        s = PresignedUrlResponseSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_missing_presigned_url_raises(self):
        data = self._valid_data()
        del data["presigned_url"]
        s = PresignedUrlResponseSerializer(data=data)
        self.assertFalse(s.is_valid())
