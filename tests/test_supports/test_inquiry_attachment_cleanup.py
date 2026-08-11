"""문의 삭제 시 첨부 S3 객체 파기.

버킷에 수명 주기 규칙이 없어(2026-08-11 확인) 코드가 지우지 않으면 첨부가 영구
잔존한다. `delete_my_inquiry`가 목적을 "개인정보를 적어 지우고 싶은 경우"로 명시
하므로, 행만 지우고 스크린샷을 남기는 것은 거짓 약속이 된다.

두 층으로 나뉜다:
- 시그널: 삭제 경로 셋(사용자 API·admin·탈퇴 CASCADE)에서 파기를 **예약**만 한다
- 태스크: 참조 확인·형식 확인·실제 삭제·재시도·최종 실패 알림
"""

import logging
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory

from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc
from apps.supports.models import Inquiry, InquiryAnswer, InquiryStatus
from apps.supports.services import delete_my_inquiry
from apps.supports.tasks import delete_inquiry_attachment_task
from apps.users.models import User

pytestmark = pytest.mark.django_db

TASK_PATH = "apps.supports.signals.signal.delete_inquiry_attachment_task.delay"


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


def _make_key() -> str:
    return s3_svc.create_key(
        action=ActionEnum.UPLOAD,
        category=CategoryEnum.INQUIRY,
        suffix=SuffixEnum.NONE,
        extension=".jpg",
    )


@pytest.fixture
def img_key() -> str:
    return _make_key()


@pytest.fixture
def inquiry(user: User, img_key: str) -> Inquiry:
    return Inquiry.objects.create(
        user=user,
        category="ACCOUNT",
        title="로그인이 안 돼요",
        content="화면 첨부합니다.",
        img_key=img_key,
    )


class TestCleanupIsScheduled:
    """시그널 층 — 세 경로 모두에서 파기가 예약되는가."""

    def test_user_delete_schedules_cleanup(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        with patch(TASK_PATH) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                delete_my_inquiry(inquiry.id, user)

        delay.assert_called_once_with(img_key)
        assert not Inquiry.objects.filter(id=inquiry.id).exists()

    def test_no_attachment_no_schedule(self, user, django_capture_on_commit_callbacks):
        bare = Inquiry.objects.create(
            user=user, category="ETC", title="첨부 없음", content="내용"
        )

        with patch(TASK_PATH) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                delete_my_inquiry(bare.id, user)

        delay.assert_not_called()

    def test_rollback_does_not_schedule(self, inquiry):
        """롤백되면 예약도 없어야 한다.

        on_commit이 아니라 post_delete에서 곧바로 예약하면, 문의는 롤백으로 살아
        있는데 첨부만 사라진다. 이 테스트가 그 구현을 떨어뜨린다.
        """
        from django.db import transaction

        with patch(TASK_PATH) as delay:
            try:
                with transaction.atomic():
                    Inquiry.objects.filter(id=inquiry.id).delete()
                    raise RuntimeError("의도적 롤백")
            except RuntimeError:
                pass

        delay.assert_not_called()
        assert Inquiry.objects.filter(id=inquiry.id).exists()

    def test_admin_single_delete_schedules_cleanup(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        """admin 단건 삭제(delete_model)도 같은 시그널을 탄다."""
        from apps.supports.admin import InquiryAdmin

        admin_obj = InquiryAdmin(Inquiry, AdminSite())
        request = RequestFactory().post("/")
        request.user = user

        with patch(TASK_PATH) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                admin_obj.delete_model(request, inquiry)

        delay.assert_called_once_with(img_key)

    def test_admin_bulk_delete_schedules_cleanup(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        from apps.supports.admin import InquiryAdmin

        admin_obj = InquiryAdmin(Inquiry, AdminSite())
        request = RequestFactory().post("/")
        request.user = user

        with patch(TASK_PATH) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                admin_obj.delete_queryset(request, Inquiry.objects.filter(id=inquiry.id))

        delay.assert_called_once_with(img_key)

    def test_withdrawal_cascade_schedules_cleanup(
        self, user, inquiry, img_key, django_capture_on_commit_callbacks
    ):
        """탈퇴 CASCADE — 개인정보 관점에서 제일 중요한 경로다."""
        with patch(TASK_PATH) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                user.delete()

        delay.assert_called_once_with(img_key)
        assert not Inquiry.objects.filter(id=inquiry.id).exists()


class TestCleanupTask:
    """태스크 층 — 실제로 지우는가, 지우면 안 될 때 멈추는가."""

    def test_deletes_object(self, img_key):
        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            delete_inquiry_attachment_task(img_key)

        s3_delete.assert_called_once_with(img_key)

    def test_skips_when_another_inquiry_still_references_key(self, user, img_key):
        """같은 key를 쓰는 문의가 남아 있으면 지우지 않는다.

        img_key에 유니크 제약이 없고 validate_attach_key도 형식·카테고리만 본다.
        그래서 답변이 달려 삭제가 막힌 문의(409)와 같은 key로 새 문의를 만든 뒤
        그것을 지우면, 무조건 삭제하는 구현에서는 **삭제 불가 문의의 첨부까지
        사라진다.** 삭제 불가라는 불변식이 우회되는 셈이다(1차 리뷰 MEDIUM).
        """
        answered = Inquiry.objects.create(
            user=user,
            category="ACCOUNT",
            title="답변 달린 문의",
            content="내용",
            img_key=img_key,
            status=InquiryStatus.ANSWERED,
        )
        InquiryAnswer.objects.filter(inquiry=answered).delete()  # 시그널 부작용 정리

        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            delete_inquiry_attachment_task(img_key)

        s3_delete.assert_not_called()
        assert Inquiry.objects.filter(id=answered.id).exists()

    def test_rejects_key_of_other_category(self, caplog):
        """문의용이 아닌 key로는 지우지 않는다 — 버킷의 임의 객체 삭제 방지."""
        dm_key = s3_svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.DM,
            suffix=SuffixEnum.NONE,
            extension=".jpg",
        )

        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            with caplog.at_level(logging.ERROR, logger="apps.supports.tasks"):
                delete_inquiry_attachment_task(dm_key)

        s3_delete.assert_not_called()
        assert "파기 거부" in caplog.text

    def test_exhausted_retries_log_error_for_alerting(self, img_key, caplog):
        """최종 실패는 ERROR로 남겨야 한다.

        Sentry LoggingIntegration 기본값이 event_level=ERROR라, WARNING이면
        알림이 뜨지 않고 컨테이너 stderr 한 줄로 끝난다. 파기 실패는 사용자에게
        한 약속이 깨진 것이라 조용히 사라지면 안 된다(1차 리뷰 MEDIUM).
        """
        task = delete_inquiry_attachment_task

        with patch("apps.supports.tasks.s3_svc.delete", side_effect=RuntimeError("S3")):
            with patch.object(task, "retry", side_effect=task.MaxRetriesExceededError()):
                with caplog.at_level(logging.ERROR, logger="apps.supports.tasks"):
                    with pytest.raises(task.MaxRetriesExceededError):
                        task(img_key)

        assert "파기 실패" in caplog.text
        assert img_key in caplog.text
