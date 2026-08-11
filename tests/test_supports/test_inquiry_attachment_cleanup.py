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
from apps.supports.models import Inquiry, InquiryStatus
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

        Sentry LoggingIntegration 기본값이 event_level=ERROR라, WARNING이면 알림이
        뜨지 않고 컨테이너 stderr 한 줄로 끝난다. 파기 실패는 사용자에게 한 약속이
        깨진 것이라 조용히 사라지면 안 된다(1차 리뷰 MEDIUM).

        **retry를 mock하지 않는다.** 이전 판은 `retry`에
        `MaxRetriesExceededError`를 side_effect로 물려 검증했는데, celery는 exc가
        주어지면 소진 시 **원본 예외를 다시 던지므로**(`app/task.py`:
        `if exc: raise_with_context(exc)`) 실제로는 그 예외가 나오지 않는다.
        즉 celery의 계약을 mock으로 덮어써서 존재하지 않는 경로를 검증하고 있었다
        — 테스트는 초록불인데 프로덕션 로그는 영영 비는 상태였다(2차 리뷰 MEDIUM).
        `apply(retries=max)`로 **실제 소진 상태**를 만들어 확인한다.
        """
        task = delete_inquiry_attachment_task

        with patch("apps.supports.tasks.s3_svc.delete", side_effect=RuntimeError("S3")):
            with caplog.at_level(logging.ERROR, logger="apps.supports.tasks"):
                result = task.apply(args=[img_key], retries=task.max_retries)

        assert result.failed()
        assert "파기 실패" in caplog.text
        assert img_key in caplog.text

    def test_not_exhausted_retries_do_not_log_error(self, img_key, caplog):
        """아직 재시도가 남았으면 최종 실패 로그를 남기지 않는다.

        소진 판정이 없으면 첫 실패부터 ERROR가 찍혀 알림이 무의미해진다.

        `apply(retries=0)`을 쓰면 안 된다 — eager 모드에서는 celery가 재시도
        체인을 그 자리에서 끝까지 돌려 결국 소진 상태에 도달한다. 직접 호출은
        `request.called_directly`라 retry가 즉시 원본 예외를 다시 던지므로
        (`raise_with_context(exc or Retry(...))`) "1회 실패" 상태를 정확히 만든다.
        """
        with patch("apps.supports.tasks.s3_svc.delete", side_effect=RuntimeError("S3")):
            with caplog.at_level(logging.ERROR, logger="apps.supports.tasks"):
                with pytest.raises(RuntimeError):
                    delete_inquiry_attachment_task(img_key)

        assert "파기 실패" not in caplog.text

    def test_task_routed_to_dedicated_queue(self):
        """전용 큐로 가야 알림 워커가 S3 지연에 밀리지 않는다.

        워커는 --pool=solo(순차 처리)라 같은 큐에 얹으면 파기 한 건이 알림 전체를
        붙잡는다.
        """
        assert delete_inquiry_attachment_task.queue == "s3_cleanup"

    def test_every_compose_consumes_the_queue(self):
        """큐 이름은 compose의 -Q와 **짝**이라 한쪽만 바뀌면 파기가 영구 정지한다.

        태스크 쪽만 단언하면 compose에 `-Q s3-cleanup`(하이픈) 같은 오타가 나도
        테스트는 초록불인데 메시지는 아무도 꺼내지 않는다. 실제 파일을 읽어
        확인한다(3차 리뷰 LOW).
        """
        import re
        from pathlib import Path

        queue = delete_inquiry_attachment_task.queue
        root = Path(__file__).resolve().parents[2]

        for name in [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
        ]:
            text = (root / name).read_text(encoding="utf-8")
            consumed = set()
            for group in re.findall(r"-Q\s+(\S+)", text):
                consumed.update(group.split(","))
            assert queue in consumed, (
                f"{name}이 '{queue}' 큐를 소비하지 않습니다 — 첨부 파기 메시지가 "
                f"영원히 쌓이기만 합니다. 현재 소비 큐: {sorted(consumed)}"
            )

    def test_task_is_ack_late_for_redelivery(self):
        """워커가 죽어도 재배달돼야 한다.

        기본값(acks_late=False)은 실행 시작 시점에 ack하므로, 배포 down으로 워커가
        죽으면 선점했던 메시지가 재배달 없이 증발한다. 행이 이미 지워져 key의 유일한
        사본이 그 메시지라 파기 지시 자체가 사라진다(3차 리뷰 HIGH).
        delete_object는 없는 key에도 204라 멱등하므로 재배달이 안전하다.
        """
        assert delete_inquiry_attachment_task.acks_late is True
        assert delete_inquiry_attachment_task.reject_on_worker_lost is True

    def test_broker_failure_logs_key_and_keeps_other_hooks(
        self, user, django_capture_on_commit_callbacks, caplog
    ):
        """브로커 장애로 예약이 실패해도 key가 로그에 남고 다른 훅은 계속 돈다.

        robust=True만 두면 Django가 찍는 로그의 qualname이 람다라 **key가 보이지
        않는다** — 행은 이미 지워져 무엇을 지워야 하는지 복구 불가능해진다.
        그리고 non-robust였다면 첫 예외에서 루프가 끊겨 두 번째 문의의 훅은
        아예 실행되지 않는다(3차 리뷰 HIGH / 2차 M-②).
        """
        from kombu.exceptions import OperationalError

        keys = [_make_key(), _make_key()]
        for i, k in enumerate(keys):
            Inquiry.objects.create(
                user=user, category="ETC", title=f"문의{i}", content="내용", img_key=k
            )

        with patch(TASK_PATH, side_effect=OperationalError("브로커 다운")):
            with caplog.at_level(logging.ERROR):
                with django_capture_on_commit_callbacks(execute=True):
                    user.delete()

        for k in keys:
            assert k in caplog.text, f"예약 실패 로그에 key가 없습니다: {k}"
