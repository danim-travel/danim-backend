"""시스템 발신 알림의 목록 표기 회귀 테스트.

sender=None에는 탈퇴(SET_NULL)와 시스템 발신 두 의미가 겹쳐 있다. 구분하지 않으면
문의 답변이 "탈퇴한 유저 — 문의하신 내용에 답변이 등록되었습니다"로 표시된다.
serializer 회귀이므로 supports가 아니라 notifications 아래에 둔다(2차 리뷰 LOW).
"""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.notifications.models.model import (
    SYSTEM_SENDER_NAME,
    Notification,
    NotificationType,
    TargetChoices,
)
from apps.notifications.serializers.list_serializers import NotificationListSerializer
from apps.notifications.utils.create_notification import create_noti
from apps.supports.models import Inquiry
from apps.supports.tasks import notify_inquiry_answered_task
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
        user=user, category="ACCOUNT", title="로그인이 안 돼요", content="내용"
    )


class TestSystemSenderDisplay:
    def test_list_api_shows_service_name_not_withdrawn_user(
        self, api_client, inquiry, user
    ):
        """문의 답변 알림은 "다님 고객센터"로 표시돼야 한다."""
        notify_inquiry_answered_task(inquiry.id)
        api_client.force_authenticate(user=user)

        response = api_client.get(reverse("notifications:notification_list"))

        assert response.status_code == 200
        row = next(
            r
            for r in response.data["results"]
            if r["notification_type"] == NotificationType.INQUIRY_ANSWERED
        )
        assert row["sender"]["nickname"] == SYSTEM_SENDER_NAME
        assert row["sender"]["nickname"] != "탈퇴한 유저"

    def test_withdrawn_user_notification_still_says_withdrawn(self, user, other_user):
        """시스템 발신 분기가 기존 탈퇴 표시를 덮어쓰지 않아야 한다."""
        create_noti(
            None,
            user.id,
            NotificationType.FOLLOW,
            other_user.id,
            TargetChoices.USER,
            "누군가 회원님을 팔로우 했습니다.",
        )

        noti = Notification.objects.get(receiver=user)
        data = NotificationListSerializer(noti).data
        assert data["sender"]["nickname"] == "탈퇴한 유저"
