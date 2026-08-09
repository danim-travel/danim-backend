"""1:1 문의 등록/조회 API와 답변 후처리(상태 전이·알림) 테스트."""

from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.core.storage.s3.services import ActionEnum, CategoryEnum, SuffixEnum, s3_svc
from apps.core.storage.s3.validators import is_valid_attach_key
from apps.notifications.models.model import Notification, NotificationType, TargetChoices
from apps.supports.models import Inquiry, InquiryAnswer, InquiryStatus
from apps.users.models import User

pytestmark = pytest.mark.django_db


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


@pytest.fixture
def other_user() -> User:
    return User.objects.create_user(
        email="other@danim.kr",
        password="Password!234",
        nickname="other",
        name="타인",
        birth_day="2000-01-01",
        is_active=True,
    )


@pytest.fixture
def inquiry(user: User) -> Inquiry:
    return Inquiry.objects.create(
        user=user,
        category="ACCOUNT",
        title="로그인이 안 돼요",
        content="비밀번호를 바꿨는데도 안 됩니다.",
    )


class TestInquiryCreate:
    def test_create_success(self, api_client, user):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {
                "category": "POST",
                "title": "게시글 삭제 문의",
                "content": "삭제한 글이 남아 있어요.",
            },
            format="json",
        )

        assert response.status_code == 201
        assert response.data["status"] == InquiryStatus.PENDING
        assert response.data["answer"] is None
        assert Inquiry.objects.filter(user=user, title="게시글 삭제 문의").exists()

    def test_requires_authentication(self, api_client):
        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "ETC", "title": "제목", "content": "내용"},
            format="json",
        )

        assert response.status_code == 401

    def test_invalid_category_rejected(self, api_client, user):
        api_client.force_authenticate(user=user)

        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "UNKNOWN", "title": "제목", "content": "내용"},
            format="json",
        )

        assert response.status_code == 400

    def test_valid_inquiry_image_key_accepted(self, api_client, user):
        api_client.force_authenticate(user=user)
        key = s3_svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.INQUIRY,
            suffix=SuffixEnum.NONE,
            extension=".jpg",
        )

        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {
                "category": "ETC",
                "title": "첨부 있음",
                "content": "내용",
                "image_key": key,
            },
            format="json",
        )

        assert response.status_code == 201
        assert Inquiry.objects.get(title="첨부 있음").image_key == key

    def test_image_key_from_other_category_rejected(self, api_client, user):
        """DM용으로 발급된 key를 문의에 붙이면 거부된다(교차 카테고리 세탁 차단).

        key를 문자열로 박아두면 S3_PREFIX/S3_PATH 설정이 바뀌었을 때 형식 오류로
        400이 나서, 정작 검증하려던 "카테고리 불일치 차단"을 증명하지 못한다.
        실제 발급기로 만든 유효한 DM key를 쓴다.
        """
        api_client.force_authenticate(user=user)
        dm_key = s3_svc.create_key(
            action=ActionEnum.UPLOAD,
            category=CategoryEnum.DM,
            suffix=SuffixEnum.NONE,
            extension=".jpg",
        )
        # 그 key가 DM 카테고리로는 유효하다는 것을 먼저 고정한다 — 아래 400이
        # 형식 문제가 아니라 카테고리 문제임을 보장한다.
        assert is_valid_attach_key(dm_key, CategoryEnum.DM)

        response = api_client.post(
            reverse("supports:inquiry_list_create"),
            {"category": "ETC", "title": "제목", "content": "내용", "image_key": dm_key},
            format="json",
        )

        assert response.status_code == 400
        assert not Inquiry.objects.filter(title="제목").exists()


class TestInquiryList:
    def test_only_own_inquiries(self, api_client, user, other_user, inquiry):
        Inquiry.objects.create(
            user=other_user, category="ETC", title="남의 문의", content="보이면 안 됨"
        )
        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("supports:inquiry_list_create"))

        assert response.status_code == 200
        titles = [row["title"] for row in response.data["results"]]
        assert titles == [inquiry.title]

    def test_requires_authentication(self, api_client):
        response = api_client.get(reverse("supports:inquiry_list_create"))

        assert response.status_code == 401


class TestInquiryDetail:
    def test_detail_includes_answer(self, api_client, user, inquiry):
        InquiryAnswer.objects.create(inquiry=inquiry, content="확인 후 조치했습니다.")
        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("supports:inquiry_detail", args=[inquiry.id]))

        assert response.status_code == 200
        assert response.data["answer"]["content"] == "확인 후 조치했습니다."
        assert response.data["status"] == InquiryStatus.ANSWERED

    def test_others_inquiry_is_404_not_403(self, api_client, other_user, inquiry):
        """403이면 그 ID의 문의가 존재한다는 사실이 새어 나간다."""
        api_client.force_authenticate(user=other_user)

        response = api_client.get(reverse("supports:inquiry_detail", args=[inquiry.id]))

        assert response.status_code == 404


class TestInquiryDelete:
    def test_pending_inquiry_deleted(self, api_client, user, inquiry):
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            reverse("supports:inquiry_detail", args=[inquiry.id])
        )

        assert response.status_code == 204
        assert not Inquiry.objects.filter(id=inquiry.id).exists()

    def test_answered_inquiry_cannot_be_deleted(
        self, api_client, user, inquiry, django_capture_on_commit_callbacks
    ):
        """답변 후 삭제를 허용하면 운영 처리 이력이 사라진다."""
        with patch("apps.supports.signals.signal.notify_inquiry_answered_task.delay"):
            with django_capture_on_commit_callbacks(execute=True):
                InquiryAnswer.objects.create(inquiry=inquiry, content="답변")
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            reverse("supports:inquiry_detail", args=[inquiry.id])
        )

        assert response.status_code == 409
        assert Inquiry.objects.filter(id=inquiry.id).exists()

    def test_closed_inquiry_cannot_be_deleted(self, api_client, user, inquiry):
        """운영진이 스팸으로 종결한 건도 사용자가 되돌릴 대상이 아니다."""
        Inquiry.objects.filter(id=inquiry.id).update(status=InquiryStatus.CLOSED)
        api_client.force_authenticate(user=user)

        response = api_client.delete(
            reverse("supports:inquiry_detail", args=[inquiry.id])
        )

        assert response.status_code == 409

    def test_others_inquiry_delete_is_404(self, api_client, other_user, inquiry):
        api_client.force_authenticate(user=other_user)

        response = api_client.delete(
            reverse("supports:inquiry_detail", args=[inquiry.id])
        )

        assert response.status_code == 404
        assert Inquiry.objects.filter(id=inquiry.id).exists()


class TestAdminCloseAction:
    def test_closes_only_unanswered(
        self, inquiry, user, django_capture_on_commit_callbacks
    ):
        """답변이 달린 문의를 CLOSED로 덮으면 처리 이력이 흐려진다."""
        from django.contrib.admin.sites import AdminSite
        from django.test import RequestFactory

        from apps.supports.admin import InquiryAdmin

        answered = Inquiry.objects.create(
            user=user, category="ETC", title="답변된 문의", content="내용"
        )
        with patch("apps.supports.signals.signal.notify_inquiry_answered_task.delay"):
            with django_capture_on_commit_callbacks(execute=True):
                InquiryAnswer.objects.create(inquiry=answered, content="답변")

        admin_obj = InquiryAdmin(Inquiry, AdminSite())
        request = RequestFactory().post("/")
        request.user = user
        with patch.object(admin_obj, "message_user"):
            admin_obj.close_inquiries(request, Inquiry.objects.all())

        inquiry.refresh_from_db()
        answered.refresh_from_db()
        assert inquiry.status == InquiryStatus.CLOSED
        assert answered.status == InquiryStatus.ANSWERED


class TestAnswerSideEffects:
    def test_answer_marks_answered_and_schedules_notification(
        self, inquiry, django_capture_on_commit_callbacks
    ):
        with patch(
            "apps.supports.signals.signal.notify_inquiry_answered_task.delay"
        ) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                InquiryAnswer.objects.create(inquiry=inquiry, content="답변입니다.")

        inquiry.refresh_from_db()
        assert inquiry.status == InquiryStatus.ANSWERED
        delay.assert_called_once_with(inquiry.id)

    def test_answer_update_does_not_renotify(
        self, inquiry, django_capture_on_commit_callbacks
    ):
        """오탈자 수정마다 알림이 다시 가면 사용자에게 소음이 된다."""
        with django_capture_on_commit_callbacks(execute=True):
            answer = InquiryAnswer.objects.create(inquiry=inquiry, content="초안")

        with patch(
            "apps.supports.signals.signal.notify_inquiry_answered_task.delay"
        ) as delay:
            with django_capture_on_commit_callbacks(execute=True):
                answer.content = "오탈자 수정본"
                answer.save()

        delay.assert_not_called()


class TestNotifyInquiryAnsweredTask:
    def test_creates_system_notification(self, inquiry, user):
        from apps.supports.tasks import notify_inquiry_answered_task

        notify_inquiry_answered_task(inquiry.id)

        noti = Notification.objects.get(receiver=user)
        assert noti.sender is None
        assert noti.notification_type == NotificationType.INQUIRY_ANSWERED
        assert noti.target_type == TargetChoices.INQUIRY
        assert noti.target_id == inquiry.id

    def test_deleted_inquiry_is_skipped(self, inquiry):
        from apps.supports.tasks import notify_inquiry_answered_task

        inquiry_id = inquiry.id
        inquiry.delete()

        notify_inquiry_answered_task(inquiry_id)

        assert not Notification.objects.filter(target_id=inquiry_id).exists()

    def test_notification_survives_blocked_relationship(self, inquiry, user):
        """차단 게이트를 타지 않는다 — 사용자가 요청한 답변은 사회적 관계로 막지 않는다."""
        from apps.supports.tasks import notify_inquiry_answered_task

        with patch("apps.blocks.services.is_blocked_between", return_value=True):
            notify_inquiry_answered_task(inquiry.id)

        assert Notification.objects.filter(receiver=user, target_id=inquiry.id).exists()
