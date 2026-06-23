from django.test import TestCase

from apps.core.utils.base62 import decode_cursor, encode_cursor


class Base64Test(TestCase):

    def test_round_trip(self):
        word = "word"
        self.assertEqual(word, decode_cursor(encode_cursor(word)))
