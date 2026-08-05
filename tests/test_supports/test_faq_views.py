"""FAQ 챗봇 조회/피드백 API 테스트."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.supports.models import FAQ, FAQCategory, FAQFeedback
from apps.supports.services import invalidate_faq_cache
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clean_faq_cache():
    """테스트 간 캐시 오염 방지"""
    invalidate_faq_cache()
    yield
    invalidate_faq_cache()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def category() -> FAQCategory:
    return FAQCategory.objects.create(name="계정", order=1)


@pytest.fixture
def faq(category: FAQCategory) -> FAQ:
    return FAQ.objects.create(
        category=category,
        question="비밀번호를 잊어버렸어요",
        answer="로그인 화면에서 '비밀번호 찾기'를 눌러주세요.",
        order=1,
    )


class TestFAQCategoryList:
    def test_active_categories_ordered(self, api_client, category):
        FAQCategory.objects.create(name="게시글", order=2)
        FAQCategory.objects.create(name="숨김", order=0, is_active=False)

        response = api_client.get(reverse("supports:faq_categories"))

        assert response.status_code == 200
        names = [c["name"] for c in response.data["categories"]]
        assert names == ["계정", "게시글"]  # order 순, 비활성 제외
        assert response.data["categories"][0]["category_id"] == str(category.id)


class TestFAQList:
    def test_requires_category_param(self, api_client):
        response = api_client.get(reverse("supports:faq_list"))
        assert response.status_code == 400

    def test_unknown_category_404(self, api_client):
        response = api_client.get(
            reverse("supports:faq_list"), {"category": "01UNKNOWNCATEGORYID0000000"}
        )
        assert response.status_code == 404

    def test_inactive_category_404(self, api_client, category):
        category.is_active = False
        category.save()

        response = api_client.get(
            reverse("supports:faq_list"), {"category": str(category.id)}
        )
        assert response.status_code == 404

    def test_active_faqs_only_ordered(self, api_client, category, faq):
        FAQ.objects.create(category=category, question="두번째", answer="답", order=2)
        FAQ.objects.create(
            category=category, question="숨김", answer="답", order=0, is_active=False
        )

        response = api_client.get(
            reverse("supports:faq_list"), {"category": str(category.id)}
        )

        assert response.status_code == 200
        questions = [f["question"] for f in response.data["faqs"]]
        assert questions == ["비밀번호를 잊어버렸어요", "두번째"]
        assert "answer" not in response.data["faqs"][0]  # 답변은 상세에서만


class TestFAQDetail:
    def test_detail_ok(self, api_client, faq):
        response = api_client.get(
            reverse("supports:faq_detail", kwargs={"faq_id": str(faq.id)})
        )

        assert response.status_code == 200
        assert response.data["faq_id"] == str(faq.id)
        assert response.data["answer"] == faq.answer

    def test_inactive_faq_404(self, api_client, faq):
        faq.is_active = False
        faq.save()

        response = api_client.get(
            reverse("supports:faq_detail", kwargs={"faq_id": str(faq.id)})
        )
        assert response.status_code == 404

    def test_faq_under_inactive_category_404(self, api_client, category, faq):
        category.is_active = False
        category.save()

        response = api_client.get(
            reverse("supports:faq_detail", kwargs={"faq_id": str(faq.id)})
        )
        assert response.status_code == 404


class TestFAQFeedback:
    def _url(self, faq: FAQ) -> str:
        return reverse("supports:faq_feedback", kwargs={"faq_id": str(faq.id)})

    def test_anonymous_feedback_created(self, api_client, faq):
        response = api_client.post(self._url(faq), {"is_helpful": False})

        assert response.status_code == 201
        feedback = FAQFeedback.objects.get(faq=faq)
        assert feedback.is_helpful is False
        assert feedback.user is None

    def test_authenticated_feedback_records_user(self, api_client, faq):
        user = User.objects.create_user(
            email="user@danim.kr",
            password="Password!234",
            nickname="tester",
            name="테스터",
            birth_day="2000-01-01",
        )
        api_client.force_authenticate(user=user)

        response = api_client.post(self._url(faq), {"is_helpful": True})

        assert response.status_code == 201
        assert FAQFeedback.objects.get(faq=faq).user == user

    def test_missing_is_helpful_400(self, api_client, faq):
        response = api_client.post(self._url(faq), {})
        assert response.status_code == 400

    def test_unknown_faq_404(self, api_client):
        response = api_client.post(
            reverse(
                "supports:faq_feedback",
                kwargs={"faq_id": "01UNKNOWNFAQID000000000000"},
            ),
            {"is_helpful": True},
        )
        assert response.status_code == 404


class TestFAQCacheInvalidation:
    """admin 저장(post_save 시그널) 시 캐시가 비워져 즉시 반영되는지"""

    def test_category_change_reflected_immediately(self, api_client, category):
        url = reverse("supports:faq_categories")
        api_client.get(url)  # 캐시 적재

        category.name = "계정/로그인"
        category.save()  # 시그널 → 캐시 무효화

        response = api_client.get(url)
        assert response.data["categories"][0]["name"] == "계정/로그인"

    def test_faq_change_reflected_immediately(self, api_client, category, faq):
        list_url = reverse("supports:faq_list")
        detail_url = reverse("supports:faq_detail", kwargs={"faq_id": str(faq.id)})
        api_client.get(list_url, {"category": str(category.id)})
        api_client.get(detail_url)  # 캐시 적재

        faq.question = "비밀번호 재설정은 어떻게 하나요?"
        faq.save()  # 시그널 → 캐시 무효화

        list_response = api_client.get(list_url, {"category": str(category.id)})
        detail_response = api_client.get(detail_url)
        assert list_response.data["faqs"][0]["question"] == faq.question
        assert detail_response.data["question"] == faq.question

    def test_deactivated_faq_disappears(self, api_client, category, faq):
        detail_url = reverse("supports:faq_detail", kwargs={"faq_id": str(faq.id)})
        api_client.get(detail_url)  # 캐시 적재

        faq.is_active = False
        faq.save()

        assert api_client.get(detail_url).status_code == 404
