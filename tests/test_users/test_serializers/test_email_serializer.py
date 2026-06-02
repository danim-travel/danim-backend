from django.test import TestCase

from apps.users.serializers.email_serializer import (
    EmailSendSerializer,
    EmailVerifySerializer,
)


class EmailSendSerializerTest(TestCase):

    def test_valid_data(self):
        serializer = EmailSendSerializer(
            data={"email": "test@example.com", "purpose": "signup"}
        )
        self.assertTrue(serializer.is_valid())

    def test_missing_email(self):
        serializer = EmailSendSerializer(data={"purpose": "signup"})
        self.assertFalse(serializer.is_valid())

    def test_invalid_email(self):
        serializer = EmailSendSerializer(
            data={"email": "notanemail", "purpose": "signup"}
        )
        self.assertFalse(serializer.is_valid())

    def test_missing_purpose(self):
        serializer = EmailSendSerializer(data={"email": "test@example.com"})
        self.assertFalse(serializer.is_valid())

    def test_invalid_purpose(self):
        serializer = EmailSendSerializer(
            data={"email": "test@example.com", "purpose": "invalid"}
        )
        self.assertFalse(serializer.is_valid())


class EmailVerifySerializerTest(TestCase):

    def test_valid_data(self):
        serializer = EmailVerifySerializer(
            data={"email": "test@example.com", "purpose": "signup", "code": "123456"}
        )
        self.assertTrue(serializer.is_valid())

    def test_invalid_code_format(self):
        serializer = EmailVerifySerializer(
            data={"email": "test@example.com", "purpose": "signup", "code": "abc123"}
        )
        self.assertFalse(serializer.is_valid())

    def test_missing_code(self):
        serializer = EmailVerifySerializer(
            data={"email": "test@example.com", "purpose": "signup"}
        )
        self.assertFalse(serializer.is_valid())
