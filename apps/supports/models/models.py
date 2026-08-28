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
    """PENDING → ANSWERED는 답변 저장 시 자동 전이(signals/signal.py).

    CLOSED는 자동 전이가 없다. 사용자가 답변에 재질문하는 경로가 없어 "답변 후
    일정 기간 경과"로 상태가 달라질 이유가 없기 때문이다. 대신 스팸·중복처럼
    **답변할 가치가 없는 문의를 답변 없이 종결**하는 운영 수단으로 쓴다
    (admin의 '선택한 문의를 종결 처리' 액션).
    """

    PENDING = "PENDING", "접수"
    ANSWERED = "ANSWERED", "답변 완료"
    CLOSED = "CLOSED", "종결"


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
    img_key = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=InquiryStatus.choices, default=InquiryStatus.PENDING
    )

    class Meta:
        db_table = "inquiries"
        ordering = ["-created_at"]
        # 실제 목록 조회는 DefaultPagination의 커서 정렬(-id)을 타므로 인덱스도 id로
        # 맞춘다. (user, created_at)이면 커서 페이지네이션이 이 인덱스를 쓰지 못한다.
        # ULID는 시간 순증가라 -id 정렬이 -created_at과 사실상 같은 순서를 준다.
        indexes = [models.Index(fields=["user", "id"])]
        constraints = [
            # 애플리케이션 검사(serializer)에 기대지 않는 **최종 방어선**.
            # 한 key를 두 문의가 공유하면 파기 태스크가 재시도 없이 보류하고, 대장
            # 행과 S3 객체가 회수 수단 없이 남는다(5차 리뷰 HIGH).
            #
            # 부분 유니크 인덱스는 `WHERE img_key = %s` 조회에도 그대로 쓰이므로
            # 별도 인덱스를 두지 않는다 — 파기 태스크와 등록 검증이 그 조회를 한다.
            #
            # ⚠ 이 테이블에 **다음번** 인덱스를 추가할 때는 데이터가 쌓여 있을
            #   것이므로 `AddIndexConcurrently` + `Migration.atomic = False`가
            #   필요하다. 비-CONCURRENTLY는 ShareLock으로 쓰기를 막는다.
            models.UniqueConstraint(
                fields=["img_key"],
                condition=models.Q(img_key__isnull=False),
                name="uq_inquiry_img_key",
            )
        ]

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


class PendingInquiryAttachmentDeletion(models.Model):
    """파기 지시 대장 — 지워야 할 첨부 key의 **양(positive) 기록**.

    왜 필요한가. 문의 행이 하드 삭제되면 `img_key`는 DB 어디에도 남지 않아,
    파기 지시의 유일한 사본이 브로커 메시지가 된다. 그 결과 두 문제가 동시에 생겼다.

    ① **부재로는 체크-후-행동 창이 닫히지 않는다.**
       A(key=K) 삭제 커밋 → 태스크가 `Inquiry.filter(img_key=K).exists()`로 False를
       보고 S3 왕복(최대 약 30초)을 시작 → 그 사이 같은 K로 B가 등록·커밋 → 태스크가
       **살아 있는 B의 첨부를 지운다.** 등록 시점에 `Inquiry`로 같은 검사를 걸어도
       그 구간에는 A가 이미 없고 B는 아직 없어 **두 검사가 같은 False를 본다**.
       "지워야 할 key"를 남겨 두고 **존재**로 판정해야 닫힌다(4차 리뷰).
    ② 브로커가 메시지를 잃으면 무엇을 지워야 하는지조차 복구할 수 없다.

    이름을 supports 범위로 좁혀 둔다 — 형제 도메인(게시글·댓글·DM·프로필)도 같은
    문제를 갖지만 그쪽 정리는 별도 과제(#338)이고, 공통 대장이 필요해지면 그때
    apps/core로 올리면서 설계를 맞추는 편이 낫다.

    수명: 문의 삭제와 같은 트랜잭션에서 생기고, S3 파기가 **성공한 뒤에만** 지워진다.
    남아 있는 행은 곧 "아직 파기되지 않은 개인정보"이므로 회수·감사 대상이다.
    주기 재구동은 `tasks.redrive_pending_attachment_deletions`(매일 04:00)가 한다 —
    **브로커에 내구성을 두지 않으므로 그 배치가 파기 약속의 이행 보증이다.**
    영구 실패 행의 해소(시도 횟수·포기 조건·운영자 조치 수단)는 후속 과제다(#341).
    """

    key = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pending_inquiry_attachment_deletions"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return self.key
