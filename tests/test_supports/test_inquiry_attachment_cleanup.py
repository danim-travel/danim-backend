"""문의 삭제 시 첨부 S3 객체 정리.

버킷에 수명 주기 규칙이 없어(2026-08-11 확인) 코드가 지우지 않으면 첨부가 영구
잔존한다. `delete_my_inquiry`가 목적을 "개인정보를 적어 지우고 싶은 경우"로 명시
하므로, 행만 지우고 스크린샷을 남기는 것은 거짓 약속이 된다.
"""

from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc
from apps.supports.models import Inquiry
from apps.supports.services import delete_my_inquiry
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        email="asker@danim.kr",
        password="Password!234",
        nickname="asker",
        name="문의자",
        birth_day="2000-01-01",
        is_active=True,
    )


@pytest.fixture
def img_key() -> str:
    return s3_svc.create_key(
        action=ActionEnum.UPLOAD,
        category=CategoryEnum.INQUIRY,
        suffix=SuffixEnum.NONE,
        extension=".jpg",
    )


@pytest.fixture
def inquiry(user: User, img_key: str) -> Inquiry:
    return Inquiry.objects.create(
        user=user,
        category="ACCOUNT",
        title="로그인이 안 돼요",
        content="화면 첨부합니다.",
        img_key=img_key,
    )


class TestAttachmentCleanup:
    def test_user_delete_removes_attachment(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        with patch("apps.supports.signals.signal.s3_svc.delete") as s3_delete:
            with django_capture_on_commit_callbacks(execute=True):
                delete_my_inquiry(inquiry.id, user)

        s3_delete.assert_called_once_with(img_key)
        assert not Inquiry.objects.filter(id=inquiry.id).exists()

    def test_no_attachment_no_s3_call(self, user, django_capture_on_commit_callbacks):
        bare = Inquiry.objects.create(
            user=user, category="ETC", title="첨부 없음", content="내용"
        )

        with patch("apps.supports.signals.signal.s3_svc.delete") as s3_delete:
            with django_capture_on_commit_callbacks(execute=True):
                delete_my_inquiry(bare.id, user)

        s3_delete.assert_not_called()

    def test_rollback_keeps_attachment(self, inquiry, img_key):
        """트랜잭션이 롤백되면 첨부는 남아야 한다.

        on_commit이 아니라 post_delete에서 곧바로 지우면, 문의는 롤백으로 살아
        있는데 첨부만 사라진다. 이 테스트가 그 구현을 잡는다.
        """
        from django.db import transaction

        with patch("apps.supports.signals.signal.s3_svc.delete") as s3_delete:
            try:
                with transaction.atomic():
                    Inquiry.objects.filter(id=inquiry.id).delete()
                    raise RuntimeError("의도적 롤백")
            except RuntimeError:
                pass

        s3_delete.assert_not_called()
        assert Inquiry.objects.filter(id=inquiry.id).exists()

    def test_s3_failure_does_not_break_delete(
        self, user, inquiry, django_capture_on_commit_callbacks
    ):
        """S3 오류가 삭제를 되돌리거나 예외로 새어나가면 안 된다.

        사용자의 삭제 요청은 DB 커밋으로 이미 성립했다. 고아 객체는 로그로 남긴다.
        """
        with patch(
            "apps.supports.signals.signal.s3_svc.delete",
            side_effect=RuntimeError("S3 장애"),
        ):
            with django_capture_on_commit_callbacks(execute=True):
                delete_my_inquiry(inquiry.id, user)

        assert not Inquiry.objects.filter(id=inquiry.id).exists()

    def test_admin_delete_also_removes_attachment(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        """서비스 함수가 아니라 post_delete에 건 이유 — admin 경로도 덮여야 한다."""
        from apps.supports.admin import InquiryAdmin

        admin_obj = InquiryAdmin(Inquiry, AdminSite())
        request = RequestFactory().post("/")
        request.user = user

        with patch("apps.supports.signals.signal.s3_svc.delete") as s3_delete:
            with django_capture_on_commit_callbacks(execute=True):
                admin_obj.delete_queryset(request, Inquiry.objects.filter(id=inquiry.id))

        s3_delete.assert_called_once_with(img_key)

    def test_user_withdrawal_cascade_removes_attachment(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        """탈퇴 CASCADE도 같은 경로를 탄다 — 개인정보 관점에서 제일 중요한 경로다."""
        with patch("apps.supports.signals.signal.s3_svc.delete") as s3_delete:
            with django_capture_on_commit_callbacks(execute=True):
                user.delete()

        s3_delete.assert_called_once_with(img_key)
        assert not Inquiry.objects.filter(id=inquiry.id).exists()
