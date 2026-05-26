import secrets


def generate_6digits_safe():
    """6자리 인증코드 발급을 위한 함수"""
    return f"{secrets.randbelow(1000000):06d}"


def generate_token():
    """sms_token 및 email_token 발급을 위한 함수"""
    return secrets.token_urlsafe(32)
