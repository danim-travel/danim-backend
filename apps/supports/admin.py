from typing import Any

from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html

from apps.supports.models import (
    FAQ,
    FAQCategory,
    FAQFeedback,
    Inquiry,
    InquiryAnswer,
    InquiryStatus,
)

# 키를 str로 고정한다 — Inquiry.status는 CharField라 런타임 값이 평범한 str이고,
# dict를 InquiryStatus로 좁히면 .get(obj.status, ...) 조회가 타입에서 어긋난다.
_STATUS_COLORS: dict[str, str] = {
    InquiryStatus.PENDING: "#d93025",
    InquiryStatus.ANSWERED: "#188038",
    InquiryStatus.CLOSED: "#5f6368",
}


class FAQInline(admin.TabularInline):
    """카테고리 화면에서 하위 질문을 한눈에 보고 바로 편집"""

    model = FAQ
    fields = ("question", "order", "is_active")
    extra = 1
    show_change_link = True  # 답변 본문은 링크 타고 들어가서 편집


@admin.register(FAQCategory)
class FAQCategoryAdmin(admin.ModelAdmin):
    """챗봇 카테고리 관리 — 목록에서 순서/활성화 바로 편집"""

    list_display = ("name", "order", "is_active", "faq_count")
    list_editable = ("order", "is_active")
    ordering = ("order",)
    inlines = [FAQInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[FAQCategory]:
        # 행마다 count 쿼리가 나가는 N+1 방지 — annotate로 1쿼리
        return super().get_queryset(request).annotate(_faq_count=Count("faqs"))

    @admin.display(description="질문 수", ordering="_faq_count")
    def faq_count(self, obj: FAQCategory) -> int:
        return int(getattr(obj, "_faq_count", 0))


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """질문/답변 관리 — 저장하면 챗봇 캐시가 자동 무효화되어 즉시 반영"""

    list_display = ("question", "category", "order", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    list_editable = ("order", "is_active")
    search_fields = ("question", "answer")
    ordering = ("category", "order")
    list_select_related = ("category",)


@admin.register(FAQFeedback)
class FAQFeedbackAdmin(admin.ModelAdmin):
    """ "해결되셨나요?" 통계 조회 전용 — 어떤 FAQ가 해결을 못 하는지 보는 화면"""

    list_display = ("faq", "is_helpful", "user", "created_at")
    list_filter = ("is_helpful", "faq__category")
    ordering = ("-id",)
    show_full_result_count = False
    list_select_related = ("faq", "user")

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: FAQFeedback | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: FAQFeedback | None = None
    ) -> bool:
        return False


class AnsweredFilter(admin.SimpleListFilter):
    """기본값을 '미답변'으로 두는 필터.

    Django 기본 필터는 "전체"가 기본이라 답변 완료 건까지 섞여 나온다. 운영에서
    중요한 건 "아직 답변 안 한 문의"이므로, 아무것도 고르지 않은 상태에서 미답변만
    보이게 한다(전체를 보려면 '전체'를 명시적으로 선택).
    """

    title = "답변 여부"
    parameter_name = "answered"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [("all", "전체"), ("yes", "답변 완료")]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "all":
            return queryset
        if value == "yes":
            return queryset.filter(answer__isnull=False)
        return queryset.filter(answer__isnull=True)

    def choices(self, changelist: Any) -> Any:
        """기본 선택지의 라벨을 '미답변'으로 바꾼다(선택 없음 = 미답변)."""
        yield {
            "selected": self.value() is None,
            "query_string": changelist.get_query_string(remove=[self.parameter_name]),
            "display": "미답변",
        }
        for lookup, title in self.lookup_choices:
            yield {
                "selected": self.value() == str(lookup),
                "query_string": changelist.get_query_string(
                    {self.parameter_name: lookup}
                ),
                "display": title,
            }


class InquiryAnswerInline(admin.StackedInline):
    """문의 화면에서 바로 답변 작성 — 저장하면 상태 전이 + 알림이 자동으로 나간다."""

    model = InquiryAnswer
    extra = 1
    max_num = 1
    can_delete = False
    fields = ("content",)


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """1:1 문의 처리 화면.

    답변은 인라인으로 작성한다. 저장 시 signal이 상태를 ANSWERED로 바꾸고
    알림 태스크를 예약하므로, 상태를 손으로 바꿀 필요가 없다.
    """

    list_display = ("title", "category", "user", "status_badge", "created_at")
    list_filter = (AnsweredFilter, "category", "status")
    search_fields = ("title", "content", "user__nickname", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user",)
    inlines = [InquiryAnswerInline]
    actions = ["close_inquiries"]
    # 문의 본문은 사용자가 쓴 것이라 운영진이 고칠 수 없어야 한다. status는 CLOSED
    # 정리를 위해 남겨 둔다.
    readonly_fields = ("user", "category", "title", "content", "image_key", "created_at")

    def get_queryset(self, request: HttpRequest) -> QuerySet[Inquiry]:
        return super().get_queryset(request).select_related("answer")

    @admin.display(description="상태", ordering="status")
    def status_badge(self, obj: Inquiry) -> Any:
        return format_html(
            '<b style="color:{}">{}</b>',
            _STATUS_COLORS.get(obj.status, "#5f6368"),
            obj.get_status_display(),
        )

    @admin.action(description="선택한 문의를 종결 처리 (답변 없이 닫기)")
    def close_inquiries(self, request: HttpRequest, queryset: QuerySet) -> None:
        """스팸·중복처럼 답변할 가치가 없는 문의를 일괄 종결한다.

        답변이 달린 문의는 제외한다 — ANSWERED를 CLOSED로 덮으면 "답변했다"는
        사실이 목록에서 사라져 처리 이력이 흐려진다. queryset.update는 auto_now를
        건너뛰므로 updated_at을 명시한다.
        """
        target = queryset.filter(answer__isnull=True).exclude(status=InquiryStatus.CLOSED)
        updated = target.update(status=InquiryStatus.CLOSED, updated_at=timezone.now())
        skipped = queryset.count() - updated
        message = f"{updated}건을 종결 처리했습니다."
        if skipped:
            message += f" ({skipped}건은 이미 답변·종결된 문의라 제외)"
        self.message_user(request, message)

    def has_add_permission(self, request: HttpRequest) -> bool:
        # 문의는 사용자가 API로만 만든다.
        return False
