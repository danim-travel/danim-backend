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


class InquiryCategory(models.TextChoices):
    """문의 분류 — FAQ 카테고리(운영진이 admin에서 자유 생성)와 달리 코드 고정값이다.

    FAQ는 콘텐츠라 늘었다 줄었다 하지만, 문의 분류는 운영 담당자 배정·통계의 기준이라
    값이 바뀌면 과거 문의의 의미까지 흔들린다. DB 테이블 대신 choices로 고정한다.
    """

    ACCOUNT = "ACCOUNT", "계정"
    POST = "POST", "게시글"
    REPORT = "REPORT", "신고·차단"
    ETC = "ETC", "기타"


class InquiryStatus(models.TextChoices):
    PENDING = "PENDING", "접수"
    ANSWERED = "ANSWERED", "답변 완료"
    CLOSED = "CLOSED", "종료"


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
        constraints = [
            # 로그인 사용자는 FAQ당 응답 1개(재응답은 갱신) — 통계 중복 오염 방지.
            # 익명(user null)은 제약 대상이 아니므로 rate limit으로 방어한다.
            models.UniqueConstraint(
                fields=["faq", "user"],
                condition=models.Q(user__isnull=False),
                name="uniq_faq_feedback_per_user",
            )
        ]


class Inquiry(TimeStampModel):
    """FAQ로 해결되지 않은 사용자의 1:1 문의.

    작성은 사용자, 답변은 운영진이 Django admin에서만 한다(답변 API 없음).
    문의자 본인 외에는 조회할 수 없다 — 서비스 레이어에서 소유권을 확인한다.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="inquiries"
    )
    category = models.CharField(max_length=20, choices=InquiryCategory.choices)
    title = models.CharField(max_length=100)
    content = models.TextField()
    # presigned 발급 시 category=inquiry로 고정되며, 저장 시 validate_attach_key로
    # 형식·카테고리를 재검증한다(DM 이미지 key를 문의에 붙이는 교차 세탁 차단).
    image_key = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.PENDING
    )

    class Meta:
        db_table = "inquiries"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "created_at"])]

    def __str__(self) -> str:
        return f"[{self.get_category_display()}] {self.title}"


class InquiryAnswer(TimeStampModel):
    """문의당 답변 1개(OneToOne).

    저장하면 signal이 문의 상태를 ANSWERED로 바꾸고 알림을 예약한다
    (signals/signal.py). 답변을 수정해도 재알림하지 않는다 — 오탈자 수정마다
    사용자에게 알림이 가면 소음이 된다.
    """

    inquiry = models.OneToOneField(
        Inquiry, on_delete=models.CASCADE, related_name="answer"
    )
    content = models.TextField()

    class Meta:
        db_table = "inquiry_answers"

    def __str__(self) -> str:
        return f"{self.inquiry.title} 답변"
