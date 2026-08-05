from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, TimeStampModel


class FAQCategory(BaseModel):
    """FAQ 챗봇 첫 화면의 카테고리 버튼 (계정/게시글/신고·차단/기타 등).

    비활성화(is_active=False)하면 하위 질문까지 챗봇에서 통째로 숨겨진다.
    """

    name = models.CharField(max_length=50)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "faq_categories"
        ordering = ["order", "id"]

    def __str__(self) -> str:
        return self.name


class FAQ(TimeStampModel):
    """카테고리 하위의 질문 버튼과 미리 작성된 답변."""

    category = models.ForeignKey(
        FAQCategory, on_delete=models.CASCADE, related_name="faqs"
    )
    question = models.CharField(max_length=200)
    answer = models.TextField()
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "faqs"
        ordering = ["order", "id"]
        indexes = [models.Index(fields=["category", "order"])]

    def __str__(self) -> str:
        return self.question


class FAQFeedback(BaseModel):
    """답변 하단 "해결되셨나요?" 응답 수집.

    비로그인 사용도 허용하므로 user는 nullable. 해결 못 한 FAQ 통계로
    운영진이 FAQ를 개선하고, 추후 챗봇 고도화의 근거 데이터가 된다.
    """

    faq = models.ForeignKey(FAQ, on_delete=models.CASCADE, related_name="feedbacks")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="faq_feedbacks",
    )
    is_helpful = models.BooleanField()

    class Meta:
        db_table = "faq_feedbacks"
        indexes = [models.Index(fields=["faq", "is_helpful"])]
