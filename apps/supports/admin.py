from django.contrib import admin
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from apps.supports.models import FAQ, FAQCategory, FAQFeedback


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
