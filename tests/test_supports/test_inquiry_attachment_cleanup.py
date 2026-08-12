"""문의 삭제 시 첨부 S3 객체 파기.

버킷에 수명 주기 규칙이 없어(2026-08-11 확인) 코드가 지우지 않으면 첨부가 영구
잔존한다. `delete_my_inquiry`가 목적을 "개인정보를 적어 지우고 싶은 경우"로 명시
하므로, 행만 지우고 스크린샷을 남기는 것은 거짓 약속이 된다.

두 층으로 나뉜다:
- 시그널: 삭제 경로 셋(사용자 API·admin·탈퇴 CASCADE)에서 파기를 **예약**만 한다
- 태스크: 참조 확인·형식 확인·실제 삭제·재시도·최종 실패 알림
"""

import logging
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.admin.sites import AdminSite
from django.db import IntegrityError, connection
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.exceptions.exception import ConflictException
from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc
from apps.supports.models import Inquiry, PendingInquiryAttachmentDeletion
from apps.supports.services import create_inquiry, delete_my_inquiry
from apps.supports.tasks import (
    delete_inquiry_attachment_task,
    redrive_pending_attachment_deletions,
)
from apps.users.models import User

pytestmark = pytest.mark.django_db

TASK_PATH = "apps.supports.signals.signal.delete_inquiry_attachment_task.delay"


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


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


class TestDeletionLedger:
    """대장(PendingInquiryAttachmentDeletion) — 파기 지시의 양(positive) 기록."""

    def test_ledger_row_created_with_delete(self, user, inquiry, img_key):
        """대장은 삭제와 같은 트랜잭션에서 생겨야 브로커 유실을 견딘다."""
        with patch(TASK_PATH):
            delete_my_inquiry(inquiry.id, user)

        assert PendingInquiryAttachmentDeletion.objects.filter(key=img_key).exists()

    def test_ledger_row_not_created_on_rollback(self, inquiry, img_key):
        from django.db import transaction

        try:
            with transaction.atomic():
                Inquiry.objects.filter(id=inquiry.id).delete()
                raise RuntimeError("의도적 롤백")
        except RuntimeError:
            pass

        assert not PendingInquiryAttachmentDeletion.objects.filter(key=img_key).exists()

    def test_ledger_row_removed_only_after_success(self, img_key):
        PendingInquiryAttachmentDeletion.objects.create(key=img_key)

        with patch("apps.supports.tasks.s3_svc.delete", side_effect=RuntimeError("S3")):
            with pytest.raises(RuntimeError):
                delete_inquiry_attachment_task(img_key)
        assert PendingInquiryAttachmentDeletion.objects.filter(key=img_key).exists()

        with patch("apps.supports.tasks.s3_svc.delete"):
            delete_inquiry_attachment_task(img_key)
        assert not PendingInquiryAttachmentDeletion.objects.filter(key=img_key).exists()

    def test_pending_key_cannot_be_reused(self, api_client, user, inquiry, img_key):
        """파기 예약된 key로는 새 문의를 등록할 수 없다.

        **이번 라운드가 실제로 닫아야 했던 것이다.** 부재로 판정하면(삭제된 문의를
        `Inquiry.filter(img_key=K)`로 찾는 방식) A가 지워진 직후 구간에서 등록 검사와
        파기 태스크의 검사가 **같은 False를 본다** — A는 없고 B는 아직 없기 때문이다.
        그 창에서 B가 커밋되면 태스크가 살아 있는 B의 첨부를 지운다(4차 리뷰).
        대장에 **존재**하는지로 판정해야 닫힌다.
        """
        with patch(TASK_PATH):
            delete_my_inquiry(inquiry.id, user)

        api_client.force_authenticate(user=user)
        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "ETC", "title": "재사용", "content": "내용", "img_key": img_key},
            format="json",
        )

        assert response.status_code == 400
        assert not Inquiry.objects.filter(title="재사용").exists()

    def test_delete_then_reuse_does_not_destroy_live_attachment(
        self, api_client, user, inquiry, img_key
    ):
        """삭제 → 재사용 시도 → 파기 실행 순서에서 살아 있는 첨부가 남아야 한다.

        위 가드가 뚫리면(=B가 등록되면) 태스크가 B의 첨부를 지운다. 여기서는
        가드가 B를 막으므로 파기가 안전하게 실행된다.
        """
        with patch(TASK_PATH):
            delete_my_inquiry(inquiry.id, user)

        api_client.force_authenticate(user=user)
        api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "ETC", "title": "재사용", "content": "내용", "img_key": img_key},
            format="json",
        )

        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            delete_inquiry_attachment_task(img_key)

        # B가 만들어지지 않았으므로 파기해도 살아 있는 첨부가 없다
        s3_delete.assert_called_once_with(img_key)
        assert not Inquiry.objects.filter(img_key=img_key).exists()

    def test_live_key_cannot_be_reused(self, api_client, user, inquiry, img_key):
        """살아 있는 문의의 key는 재등록할 수 없다.

        상세 응답이 `image.key`를 그대로 돌려주므로 재제출만으로 도달 가능하다.
        대장 검사만 두면(5차 리뷰 HIGH) 이 경우가 통과해 "한 key = 한 문의"가 깨지고,
        A를 지웠을 때 태스크가 B의 참조를 보고 **재시도 없이 보류**해 대장 행과 S3
        객체가 회수 수단 없이 남는다.
        """
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "ETC", "title": "중복", "content": "내용", "img_key": img_key},
            format="json",
        )

        assert response.status_code == 400
        assert not Inquiry.objects.filter(title="중복").exists()

    def test_db_constraint_is_last_line_of_defense(self, user, inquiry, img_key):
        """serializer를 우회해도 DB가 막는다 — 그 검사도 체크-후-행동이라 필요하다."""
        from django.db import transaction

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Inquiry.objects.create(
                    user=user,
                    category="ETC",
                    title="제약 우회 시도",
                    content="내용",
                    img_key=img_key,
                )

    def test_constraint_violation_becomes_409(self, user, inquiry, img_key):
        """DB 제약 위반은 500이 아니라 409로 나가야 한다.

        serializer가 먼저 거르지만 그 검사도 체크-후-행동이라 동시 요청 둘이 각각
        통과할 수 있다 — 제약에 걸리는 쪽이 실제로 생긴다. 변환이 없으면 사용자는
        원인을 알 수 없는 500을 받는다.
        """
        with pytest.raises(ConflictException):
            create_inquiry(
                user,
                {
                    "category": "ETC",
                    "title": "동시 요청",
                    "content": "내용",
                    "img_key": img_key,
                },
            )

    def test_unrelated_integrity_error_is_not_swallowed(self, user, img_key):
        """다른 제약 위반까지 409로 바꾸면 진짜 버그가 숨는다.

        제약명 문자열 매칭이라 이름을 바꾸면 조용히 500으로 퇴행한다 — 위 테스트가
        그때 빨개진다. 이쪽은 반대 방향(과잉 변환)을 잠근다.
        """
        with patch(
            "apps.supports.services.services.Inquiry.objects.create",
            side_effect=IntegrityError('violates foreign key constraint "fk_other"'),
        ):
            with pytest.raises(IntegrityError):
                create_inquiry(
                    user,
                    {
                        "category": "ETC",
                        "title": "무관한 위반",
                        "content": "내용",
                        "img_key": img_key,
                    },
                )

    def test_ledger_delete_failure_does_not_misreport_s3(self, img_key, caplog):
        """대장 삭제 실패가 "S3 파기 실패"로 오보되면 안 된다.

        같은 try 안에 두면 이미 지운 뒤인데 "객체가 버킷에 남아 있을 수 있습니다"
        ERROR가 나가고, 재시도마다 S3 왕복을 반복한다(5차 리뷰 LOW).
        """
        PendingInquiryAttachmentDeletion.objects.create(key=img_key)

        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            with patch(
                "apps.supports.tasks.PendingInquiryAttachmentDeletion.objects"
            ) as objects:
                objects.filter.return_value.delete.side_effect = RuntimeError("DB")
                with caplog.at_level(logging.INFO, logger="apps.supports.tasks"):
                    with pytest.raises(RuntimeError):
                        delete_inquiry_attachment_task(img_key)

        s3_delete.assert_called_once_with(img_key)
        assert "파기 완료" in caplog.text
        assert "파기 실패" not in caplog.text

    def test_success_is_logged_for_audit(self, img_key, caplog):
        """파기 성공을 남긴다 — 이행 증적이자, "워커가 도는지"의 유일한 신호다."""
        with patch("apps.supports.tasks.s3_svc.delete"):
            with caplog.at_level(logging.INFO, logger="apps.supports.tasks"):
                delete_inquiry_attachment_task(img_key)

        assert "파기 완료" in caplog.text
        assert img_key in caplog.text


class TestAdminBulkDeleteLock:
    """일괄 삭제 경로의 행 잠금."""

    def test_bulk_delete_actually_emits_for_update(self, user, inquiry):
        """queryset을 super()에 넘기는 것만으로는 잠기지 않는다.

        `QuerySet.delete()`가 첫 줄에서 `del_query.query.select_for_update = False`로
        버린다(django/db/models/query.py:1232). 지연 평가라 그때까지 SQL이 나가지
        않았으므로 FOR UPDATE는 한 번도 실행되지 않는다 — 6차까지의 코드가 그랬고,
        테스트가 없어 "잠겨 있다"는 잘못된 안전망이 다섯 라운드를 살아남았다.
        """
        from django.test.utils import CaptureQueriesContext

        from apps.supports.admin import InquiryAdmin

        admin_obj = InquiryAdmin(Inquiry, AdminSite())
        request = RequestFactory().post("/")
        request.user = user

        with patch(TASK_PATH):
            with CaptureQueriesContext(connection) as ctx:
                admin_obj.delete_queryset(request, Inquiry.objects.filter(id=inquiry.id))

        sqls = [q["sql"] for q in ctx.captured_queries if "inquiries" in q["sql"]]
        assert any("FOR UPDATE" in sql for sql in sqls), (
            "일괄 삭제가 대상 행을 잠그지 않습니다 — 사용자 삭제와 경합하면 이미 "
            "삭제된 행에도 post_delete가 발송돼 같은 key가 두 번 큐잉됩니다.\n"
            + "\n".join(sqls)
        )
        assert not Inquiry.objects.filter(id=inquiry.id).exists()


class TestDedupMigration:
    """유니크 제약을 걸기 전 중복 정리 — 실패하면 배포가 멈춘다."""

    @staticmethod
    def _dedup():
        """마이그레이션 모듈은 이름이 숫자로 시작해 import 문으로 못 부른다."""
        import importlib

        from django.apps import apps as django_apps

        module = importlib.import_module(
            "apps.supports.migrations.0004_pendinginquiryattachmentdeletion_and_more"
        )
        module._null_out_duplicate_img_keys(django_apps, None)

    @pytest.mark.parametrize("dupes", [2, 3])
    def test_keeps_oldest_and_nulls_the_rest(self, user, img_key, dupes):
        """가장 오래된 1건만 key를 유지하고, 그 뒤 제약을 걸 수 있어야 한다.

        pytest는 **빈 테스트 DB**에 마이그레이션을 돌리므로 dedup이 항상 0행 no-op이다
        — 즉 이 함수를 통째로 지워도 CI는 초록불이었다(7차 리뷰). 제약을 잠시 걷고
        중복을 실제로 만들어 확인한다. DDL도 테스트 트랜잭션과 함께 롤백된다.
        """
        with connection.cursor() as cursor:
            cursor.execute("DROP INDEX uq_inquiry_img_key")

        created = [
            Inquiry.objects.create(
                user=user,
                category="ETC",
                title=f"중복{i}",
                content="내용",
                img_key=img_key,
            )
            for i in range(dupes)
        ]
        # ULID는 시간 순증가라 사전순 최솟값이 가장 먼저 만들어진 행이다.
        oldest = min(created, key=lambda o: o.id)

        self._dedup()

        survivors = list(Inquiry.objects.filter(img_key=img_key))
        assert [o.id for o in survivors] == [oldest.id], (
            "중복 정리가 가장 오래된 1건만 남기지 않았습니다 — "
            f"남은 행: {[o.id for o in survivors]}"
        )

        # 정리 후에는 제약을 걸 수 있어야 한다. 이 CREATE가 곧 AddConstraint다.
        with connection.cursor() as cursor:
            # Django는 PostgreSQL FK를 DEFERRABLE INITIALLY DEFERRED로 만든다
            # (backends/postgresql/operations.py:150 — base는 빈 문자열을 돌려준다).
            # 그래서 같은 트랜잭션의 INSERT가 남긴 AFTER 트리거가 커밋까지 대기하고,
            # PostgreSQL은 pending trigger events가 있는 테이블에 CREATE INDEX를
            # 거부한다. 미뤄 둔 트리거를 **지금 발화**시켜(검사를 끄는 게 아니다) 푼다.
            cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
            cursor.execute(
                "CREATE UNIQUE INDEX uq_inquiry_img_key ON inquiries (img_key) "
                "WHERE img_key IS NOT NULL"
            )

    def test_runs_before_the_constraint_is_added(self):
        """`operations`에서 순서가 뒤집히거나 빠지면 dedup은 존재해도 소용없다.

        위 테스트들은 함수를 직접 부르므로 `RunPython`을 통째로 빼도 통과한다 —
        마이그레이션이 그 함수를 실제로 부르는지, 그리고 `AddConstraint`보다 **먼저**
        부르는지는 여기서만 확인된다(8차 리뷰).
        """
        import importlib

        from django.db import migrations

        module = importlib.import_module(
            "apps.supports.migrations.0004_pendinginquiryattachmentdeletion_and_more"
        )
        ops = module.Migration.operations

        idx_dedup = next(
            i
            for i, op in enumerate(ops)
            if isinstance(op, migrations.RunPython)
            and op.code is module._null_out_duplicate_img_keys
        )
        idx_constraint = next(
            i for i, op in enumerate(ops) if isinstance(op, migrations.AddConstraint)
        )
        assert idx_dedup < idx_constraint, (
            "중복 정리가 AddConstraint보다 뒤에 있습니다 — 기존 중복이 있으면 "
            "제약 생성이 실패하고 배포가 그 자리에서 멈춥니다."
        )

    def test_leaves_single_use_keys_alone(self, user, inquiry, img_key):
        """중복이 아닌 행은 건드리지 않는다 — 과잉 정리 방지."""
        self._dedup()

        inquiry.refresh_from_db()
        assert inquiry.img_key == img_key


class TestRedrive:
    """대장 재구동 — 브로커를 잃어도 파기가 재개되는 유일한 경로."""

    def test_is_scheduled(self):
        """beat 스케줄이 곧 파기 약속의 이행 보증이다.

        redis에 AOF를 두지 않으므로 브로커 메시지는 언제든 사라질 수 있다. 이 항목이
        빠지면 그 순간 미파기가 **영구**가 된다(7차 리뷰).
        """
        from django.conf import settings

        entry = settings.CELERY_BEAT_SCHEDULE.get("redrive-inquiry-attachment-deletions")
        assert entry is not None, (
            "재구동 배치가 스케줄에 없습니다 — 브로커 유실 시 파기를 재개할 주체가 "
            "아무도 없습니다."
        )
        # 리터럴 대신 태스크 객체에서 뽑는다 — 문자열끼리 비교하면 registry 등록
        # 여부를 검증하지 못하고, 큐가 빠져 알림 워커(solo)에 얹혀도 아무도 못 잡는다.
        assert entry["task"] == redrive_pending_attachment_deletions.name
        assert redrive_pending_attachment_deletions.queue == "s3_cleanup"

    def test_requeues_only_unreferenced_and_aged_rows(self, user, inquiry, img_key):
        """참조가 남은 행과 갓 예약된 행은 건너뛴다."""
        orphan = _make_key()
        fresh = _make_key()
        PendingInquiryAttachmentDeletion.objects.create(key=orphan)
        PendingInquiryAttachmentDeletion.objects.create(key=fresh)
        # img_key는 살아 있는 문의(fixture)가 참조 중 — 실패가 아니라 보류다.
        PendingInquiryAttachmentDeletion.objects.create(key=img_key)

        old = timezone.now() - timedelta(hours=2)
        PendingInquiryAttachmentDeletion.objects.filter(key__in=[orphan, img_key]).update(
            created_at=old
        )

        with patch("apps.supports.tasks.delete_inquiry_attachment_task.delay") as delay:
            redrive_pending_attachment_deletions()

        assert [c.args[0] for c in delay.call_args_list] == [orphan], (
            "재구동이 고른 대상이 잘못됐습니다 — 참조가 남은 key를 다시 큐잉하면 "
            "태스크가 또 보류하고, 갓 예약된 key는 정상 경로가 아직 진행 중입니다."
        )

    def test_warns_so_the_backlog_is_visible(self, caplog):
        """조용히 재구동하면 "몇 건이 얼마나 밀렸는지"를 아무도 모른다."""
        key = _make_key()
        PendingInquiryAttachmentDeletion.objects.create(key=key)
        PendingInquiryAttachmentDeletion.objects.filter(key=key).update(
            created_at=timezone.now() - timedelta(hours=2)
        )

        with patch("apps.supports.tasks.delete_inquiry_attachment_task.delay"):
            with caplog.at_level(logging.WARNING, logger="apps.supports.tasks"):
                redrive_pending_attachment_deletions()

        assert "재구동" in caplog.text and key in caplog.text

    def test_silent_when_nothing_to_do(self, caplog):
        """평시에 매일 경고가 나가면 아무도 그 경고를 읽지 않게 된다."""
        with patch("apps.supports.tasks.delete_inquiry_attachment_task.delay") as delay:
            with caplog.at_level(logging.WARNING, logger="apps.supports.tasks"):
                redrive_pending_attachment_deletions()

        delay.assert_not_called()
        assert not [r for r in caplog.records if r.name == "apps.supports.tasks"]


class TestCleanupTask:
    """태스크 층 — 실제로 지우는가, 지우면 안 될 때 멈추는가."""

    def test_deletes_object(self, img_key):
        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            delete_inquiry_attachment_task(img_key)

        s3_delete.assert_called_once_with(img_key)

    def test_skips_when_an_inquiry_still_references_key(self, inquiry, img_key):
        """살아 있는 문의가 그 key를 참조하면 지우지 않는다 — 심층 방어.

        이제 `uq_inquiry_img_key`가 "한 key = 한 문의"를 DB에서 강제하므로 이 분기에
        정상적으로 도달할 수는 없다. 다만 제약 이전에 쌓인 행이나 serializer를
        우회하는 미래 경로를 위해 남긴다. 여기서는 아직 살아 있는 문의의 key로
        태스크를 직접 호출해(예: 중복 배달) 보존 쪽으로 실패하는지 확인한다.
        """
        PendingInquiryAttachmentDeletion.objects.create(key=img_key)

        with patch("apps.supports.tasks.s3_svc.delete") as s3_delete:
            delete_inquiry_attachment_task(img_key)

        s3_delete.assert_not_called()
        assert Inquiry.objects.filter(id=inquiry.id).exists()
        # 대장 행은 **유지돼야 한다.** 여기서 지우면 다른 태스크가 그 사이 대장이
        # 빈 것을 보고 S3 왕복을 시작해 창이 재개된다(5차 리뷰).
        assert PendingInquiryAttachmentDeletion.objects.filter(key=img_key).exists()

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
        import shlex
        from pathlib import Path

        import yaml

        queue = delete_inquiry_attachment_task.queue
        root = Path(__file__).resolve().parents[2]

        for name in [
            "docker-compose.yml",
            "docker-compose.dev.yml",
            "docker-compose.prod.yml",
        ]:
            # 전문 정규식은 주석의 `-Q ...`까지 읽어, 서비스를 통째로 주석 처리해도
            # 초록불이 된다. YAML을 파싱해 **실제 command**만 본다.
            spec = yaml.safe_load((root / name).read_text(encoding="utf-8"))
            consumed: set[str] = set()
            for svc in (spec.get("services") or {}).values():
                cmd = svc.get("command")
                if not cmd:
                    continue
                tokens = shlex.split(cmd if isinstance(cmd, str) else " ".join(cmd))
                for i, tok in enumerate(tokens):
                    if tok == "-Q" and i + 1 < len(tokens):
                        consumed.update(tokens[i + 1].split(","))
            assert queue in consumed, (
                f"{name}의 어떤 서비스도 '{queue}' 큐를 소비하지 않습니다 — 첨부 파기 "
                f"메시지가 영원히 쌓이기만 합니다. 현재 소비 큐: {sorted(consumed)}"
            )

    def test_dev_and_prod_redis_has_no_write_denying_limit(self):
        """redis에 상한을 두지 않았음을 잠근다 — 같은 하네스로.

        `-Q` 오타를 막으려 만든 YAML 파싱을 더 위험한 문자열에도 적용한다(7차 리뷰).

        상한을 **넣지 않았음**을 단언한다. 메모리(`--maxmemory`)든 디스크
        (`--appendonly`)든, 상한에 닿으면 redis는 쓰기를 거부하고 같은 인스턴스의
        `CACHES["auth"]`는 fail-closed라 그게 **로그인 500**이 된다. 5차에 메모리
        상한을, 6차까지 AOF를 넣었다가 각각 되돌린 자리라 주석만으로는 재발을 못 막는다.
        실측 후 도입은 #343이고, 그때 이 단언을 함께 바꾼다.
        """
        import shlex
        from pathlib import Path

        import yaml

        root = Path(__file__).resolve().parents[2]

        # 로컬(docker-compose.yml)은 제외한다 — auth 캐시 500이 개발자 한 명의
        # 재실행으로 끝난다.
        for name in ["docker-compose.dev.yml", "docker-compose.prod.yml"]:
            spec = yaml.safe_load((root / name).read_text(encoding="utf-8"))
            redis = (spec.get("services") or {}).get("redis") or {}
            cmd = redis.get("command") or ""
            tokens = shlex.split(cmd if isinstance(cmd, str) else " ".join(cmd))

            assert "--maxmemory" not in tokens, (
                f"{name}의 redis에 메모리 상한이 있습니다 — 이 인스턴스의 auth 캐시는 "
                "fail-closed라 상한 도달이 로그인 500이 됩니다. 실측 후 #343에서."
            )
            assert "--appendonly" not in tokens and not redis.get("volumes"), (
                f"{name}의 redis에 AOF/영속 볼륨이 있습니다 — AOF write 실패(ENOSPC 등)는 "
                "이후 모든 쓰기를 -MISCONF로 거부시켜 위와 같은 결과가 됩니다. 파기 지시의 "
                "내구성은 대장 + redrive 배치가 줍니다."
            )

    def test_task_is_ack_late_for_redelivery(self):
        """실행이 끝난 뒤에 ack해야 재배달 여지가 남는다.

        기본값(acks_late=False)은 실행 **시작** 시점에 ack하므로, 배포 down으로 워커가
        죽으면 선점했던 메시지가 재배달 없이 증발한다. 행이 이미 지워져 key의 유일한
        사본이 그 메시지라 파기 지시 자체가 사라진다(3차 리뷰 HIGH).
        delete_object는 없는 key에도 204라 멱등하므로 재배달이 안전하다.

        ⚠ 재배달 시점은 종료 방식에 따라 다르다(tasks.py의 계약 주석 참조):
          graceful 종료는 restore_at_shutdown으로 즉시, SIGKILL은
          visibility_timeout(기본 3600초)이라 **최대 1시간 뒤**다.
          `reject_on_worker_lost`는 --pool=solo에서 무동작이며(WorkerLostError는
          prefork가 자식 사망 시 올린다) 풀 교체에 대비해 켜 두는 것뿐이다.
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
