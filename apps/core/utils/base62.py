import base64
import secrets


def generate_6digits_safe():
    """6자리 인증코드 발급을 위한 함수"""
    return f"{secrets.randbelow(1000000):06d}"


def generate_token():
    """sms_token 및 email_token 발급을 위한 함수"""
    return secrets.token_urlsafe(32)


def encode_cursor(cursor):
    return base64.b64encode(cursor.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor):
    return base64.b64decode(cursor.encode("utf-8")).decode("utf-8")
