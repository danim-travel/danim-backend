"""캐시 장애 정책(이원화) 회귀 테스트.

과거 base의 IGNORE_EXCEPTIONS=True를 dev/prod/local이 CACHES 재정의로 누락시켜
환경별로 정책이 갈라졌다 — 어떤 환경은 Redis 장애 시 "로그아웃된 토큰이
재발급되는 fail-open", 다른 환경은 "피드/검색 전면 500". 여기서는
default(fail-open 편의 캐시) / auth(fail-closed 보안 키) 이원화 계약과,
보안 모듈들이 실제로 auth 별칭에 바인딩돼 있음을 고정한다.
"""

from django.conf import settings
from django.core.cache import caches
from django.test import TestCase


class CachePolicyTest(TestCase):

    def test_both_aliases_exist(self):
        self.assertIn("default", settings.CACHES)
        self.assertIn("auth", settings.CACHES)

    def test_default_alias_is_fail_open(self):
        """편의 캐시(피드·검색·presence·unread)는 Redis 장애 시 miss로 동작해야 한다."""
        options = settings.CACHES["default"]["OPTIONS"]
        self.assertTrue(options.get("IGNORE_EXCEPTIONS"))

    def test_auth_alias_is_fail_closed(self):
        """보안 키(블랙리스트·인증코드·소켓키)는 장애를 삼키면 안 된다.

        IGNORE_EXCEPTIONS가 True면 블랙리스트 조회가 장애 시 None을 돌려줘
        로그아웃된 토큰이 재발급된다(fail-open) — 반드시 예외가 나야 한다.
        """
        options = settings.CACHES["auth"].get("OPTIONS", {})
        self.assertFalse(options.get("IGNORE_EXCEPTIONS", False))

    def test_security_modules_bind_auth_alias(self):
        """보안 모듈이 default가 아닌 auth 별칭을 쓰는지 고정 (조용한 회귀 방지)."""
        from apps.core.websocket.websocket_key.service import key_service  # noqa: F401
        from apps.users.services import (
            email_service,
            login_logout_service,
            reset_password_service,
            signup_service,
            token_service,
        )

        auth_cache = caches["auth"]
        for module in (
            token_service,
            login_logout_service,
            email_service,
            reset_password_service,
            signup_service,
        ):
            self.assertIs(
                module.cache,
                auth_cache,
                f"{module.__name__}.cache가 auth 별칭이 아닙니다",
            )
