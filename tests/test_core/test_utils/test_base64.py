import base64

from django.test import TestCase

from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import decode_cursor, encode_cursor


class Base64Test(TestCase):

    def test_round_trip(self):
        word = "word"
        self.assertEqual(word, decode_cursor(encode_cursor(word)))

    def test_invalid_base64_raises_validation_exception(self):
        """base64 로 디코드 자체가 안 되는 문자열 (cursor=abc 재현 케이스) -> 500 대신 400"""
        with self.assertRaises(ValidationException):
            decode_cursor("abc")

    def test_non_utf8_bytes_raises_validation_exception(self):
        """base64 디코드는 되지만 결과 바이트가 utf-8이 아닌 경우"""
        invalid_utf8 = base64.b64encode(b"\xff\xfe").decode("utf-8")
        with self.assertRaises(ValidationException):
            decode_cursor(invalid_utf8)
