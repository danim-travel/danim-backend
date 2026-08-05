"""admin 활성화 스모크 테스트.

브라우저로 열어봐야만 확인되던 경로(superuser 생성 → 로그인 → admin 진입,
프록시 뒤 CSRF Origin 검사, read-only 권한, prod 보안 설정)를 기계 검증한다.
"""

import importlib
import sys

import pytest
from django.contrib import admin as django_admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import Client, RequestFactory
from django.urls import reverse

from apps.posts.models import Post

SUPERUSER_KWARGS = {
    "email": "admin@danim.kr",
    "password": "AdminPass!234",
    "nickname": "admin",
    "name": "관리자",
    "birth_day": "1990-01-01",
}


@pytest.mark.django_db
class TestCreateSuperuser:
    def test_superuser_is_active_and_verified(self):
        user = get_user_model().objects.create_superuser(**SUPERUSER_KWARGS)
        assert user.is_active is True
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.is_email_verified is True

    def test_superuser_can_login_and_open_admin(self, client):
        get_user_model().objects.create_superuser(**SUPERUSER_KWARGS)
        assert client.login(
            email=SUPERUSER_KWARGS["email"], password=SUPERUSER_KWARGS["password"]
        )
        response = client.get(reverse("admin:index"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestAdminAccess:
    def test_anonymous_is_redirected_to_login(self, client):
        response = client.get(reverse("admin:index"))
        assert response.status_code == 302

    def test_admin_login_post_passes_csrf_origin_check_behind_proxy(self, settings):
        """nginx(TLS 종료) 뒤 시나리오 재현 — SECURE_PROXY_SSL_HEADER가 없으면
        Origin(https) != good_origin(http) 불일치로 403이 나는 회귀를 방지한다.

        CSRF_TRUSTED_ORIGINS는 일부러 설정하지 않는다 — 설정하면 Origin 정확일치로
        통과해 버려서 프록시 헤더가 유일한 통과 경로라는 검증이 무력화된다."""
        settings.SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

        get_user_model().objects.create_superuser(**SUPERUSER_KWARGS)
        csrf_client = Client(enforce_csrf_checks=True)
        login_url = reverse("admin:login")

        csrf_client.get(login_url, HTTP_X_FORWARDED_PROTO="https")
        csrftoken = csrf_client.cookies["csrftoken"].value
        response = csrf_client.post(
            login_url,
            {
                "username": SUPERUSER_KWARGS["email"],
                "password": SUPERUSER_KWARGS["password"],
                "csrfmiddlewaretoken": csrftoken,
                "next": reverse("admin:index"),
            },
            HTTP_X_FORWARDED_PROTO="https",
            HTTP_ORIGIN="https://testserver",
        )
        assert response.status_code != 403


@pytest.mark.django_db
class TestReadOnlyAdmin:
    def test_post_admin_is_fully_readonly(self):
        admin_instance = django_admin.site._registry[Post]
        request = RequestFactory().get("/")
        request.user = get_user_model().objects.create_superuser(**SUPERUSER_KWARGS)

        assert admin_instance.has_add_permission(request) is False
        assert admin_instance.has_change_permission(request) is False
        assert admin_instance.has_delete_permission(request) is False

    def test_user_admin_cannot_add_or_delete(self):
        user_model = get_user_model()
        admin_instance = django_admin.site._registry[user_model]
        request = RequestFactory().get("/")
        request.user = user_model.objects.create_superuser(**SUPERUSER_KWARGS)

        assert admin_instance.has_add_permission(request) is False
        assert admin_instance.has_delete_permission(request) is False


class TestProdSettingsGuard:
    """prod 설정 모듈이 프록시 HTTPS 인식·시큐어 쿠키·ADMIN_URL 강제를 갖췄는지
    import 수준에서 검증 (DB 불필요)."""

    PROD_ENV = {
        "ALLOWED_HOSTS": "api.danim.kr",
        "CORS_ALLOWED_ORIGINS": "https://danim.kr",
        "DB_NAME": "check",
        "DB_USER": "check",
        "DB_PASSWORD": "check",
        "DB_HOST": "localhost",
    }

    def _fresh_import_prod(self):
        # 원본 모듈을 보관했다가 복원 — 이후 테스트가 재실행된 top-level
        # (read_env, sentry init)을 보지 않도록 격리한다
        originals = {
            name: sys.modules.pop(name, None)
            for name in ("config.settings.prod", "config.settings.base")
        }
        try:
            return importlib.import_module("config.settings.prod")
        finally:
            for name, module in originals.items():
                if module is not None:
                    sys.modules[name] = module
                else:
                    sys.modules.pop(name, None)

    def test_prod_defines_proxy_ssl_and_secure_cookies(self, monkeypatch):
        for key, value in self.PROD_ENV.items():
            monkeypatch.setenv(key, value)
        monkeypatch.setenv("ADMIN_URL", "ops-test-path/")

        prod = self._fresh_import_prod()

        assert prod.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
        assert prod.SESSION_COOKIE_SECURE is True
        assert prod.CSRF_COOKIE_SECURE is True
        assert prod.CSRF_TRUSTED_ORIGINS
        assert prod.ADMIN_URL == "ops-test-path/"

    def test_prod_rejects_default_admin_url(self, monkeypatch):
        for key, value in self.PROD_ENV.items():
            monkeypatch.setenv(key, value)
        monkeypatch.delenv("ADMIN_URL", raising=False)

        with pytest.raises(ImproperlyConfigured):
            self._fresh_import_prod()
