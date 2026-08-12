from typing import Any, cast

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import Count, Exists, Field, OuterRef, QuerySet
from django.http import HttpRequest
from django.utils import timezone
from django.utils.html import format_html

from apps.core.storage.s3 import s3_svc
from apps.supports.models import (
    FAQ,
    FAQCategory,
    FAQFeedback,
    Inquiry,
    InquiryAnswer,
    InquiryStatus,
    PendingInquiryAttachmentDeletion,
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
    # 문의 본문은 사용자가 쓴 것이라 운영진이 고칠 수 없어야 한다.
    # status도 읽기전용이다 — 전이는 답변 저장(signal)과 종결 액션 두 경로만 갖는데,
    # 자유 편집이 열려 있으면 그 상태 기계를 우회해 ANSWERED로 바꿔 놓고 답변이 없는
    # 조합이 만들어진다.
    readonly_fields = (
        "user",
        "category",
        "title",
        "content",
        "image_preview",
        "status",
        "created_at",
    )
    exclude = ("img_key",)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Inquiry]:
        return super().get_queryset(request).select_related("answer")

    def save_model(
        self, request: HttpRequest, obj: Inquiry, form: Any, change: bool
    ) -> None:
        """기존 문의 행은 admin에서 저장하지 않는다 — 2차 방어.

        아래 get_object의 잠금이 부활 경로를 막지만, 그 방어는 **get_object를 지나는
        요청에만** 걸린다. `list_editable`이 추가되면 changelist POST가 get_object를
        거치지 않고 바로 save_model로 오므로 방어가 통째로 사라진다. 같은 파일의
        FAQCategoryAdmin·FAQAdmin이 이미 list_editable을 쓰고 있어 충분히 일어날 수
        있는 변경이다. 여기서 한 번 더 막으면 그 변경에 면역이 된다.

        건너뛰어도 잃는 것이 없다: 이 화면의 Inquiry 필드는 전부 readonly라 change
        저장은 실질적으로 no-op이고, 상태 전이는 답변 저장(signal)과 종결 액션의
        `queryset.update()`가 담당한다. 둘 다 이 경로를 지나지 않는다.

        ⚠ 나중에 편집 가능한 Inquiry 필드가 생기면 그 수정이 조용히 사라진다.
          `test_all_inquiry_fields_are_readonly`가 그때 깨져 이 주석으로 데려온다.
        """
        if not change:
            super().save_model(request, obj, form, change)

    def delete_queryset(self, request: HttpRequest, queryset: QuerySet) -> None:
        """일괄 삭제도 대상 행을 먼저 잠근다.

        `delete_selected`는 changelist에서 실행되는데 `changelist_view`는 atomic이
        아니라(원본 확인) 여기서 트랜잭션을 직접 연다. 잠그지 않으면 운영자 둘이 같은
        문의를 동시에 건드릴 때 COMMIT 시 IntegrityError가 난다 — Collector.delete()가
        atomic이라 부분 삭제 없이 전체 롤백되므로 조용한 소실은 아니지만, 사용자
        삭제와 순서를 맞추면 애초에 나지 않는다.

        ⚠ **잠금 queryset을 super()에 넘기는 것만으로는 잠기지 않는다.**
          `QuerySet.delete()`가 첫 줄에서 `del_query.query.select_for_update = False`로
          **버린다**(django/db/models/query.py:1232). 지연 평가라 그때까지 SQL이 나가지
          않았으므로 FOR UPDATE는 한 번도 실행되지 않는다. `list(...)`로 **여기서 먼저
          평가**해야 실제로 잠긴다(6차 리뷰).

          안 잠그면: 운영자가 대상을 수집한 뒤 사용자가 같은 행을 지우고 커밋해도,
          collector는 이미 수집한 인스턴스 전부에 `post_delete`를 **무조건** 보낸다
          (deletion.py — `if count:`는 카운터만 감싼다). 같은 key로 파기 태스크가 두 번
          큐잉된다. 태스크가 멱등이라 손상은 없지만 "여기는 잠겨 있다"는 잘못된 안전망이
          더 비싸다.
        """
        with transaction.atomic():
            pks = list(queryset.values_list("pk", flat=True))
            list(Inquiry.objects.select_for_update(of=("self",)).filter(pk__in=pks))
            super().delete_queryset(request, Inquiry.objects.filter(pk__in=pks))

    def get_object(
        self, request: HttpRequest, object_id: str, from_field: str | None = None
    ) -> Inquiry | None:
        """저장(POST) 시 대상 문의 행을 잠근 뒤 읽는다.

        사용자 삭제(services.delete_my_inquiry)도 같은 행을 select_for_update로
        잠그므로, 둘 중 뒤에 온 쪽이 대기한다. 이 잠금이 없으면 다음이 일어난다:
          ① 운영자가 답변 화면을 열어 문의를 읽는다
          ② 사용자가 그 문의를 삭제하고 커밋한다
          ③ 운영자가 저장을 누른다 → save_model의 obj.save()가 UPDATE를 날리는데
             0행이다. Django `Model._save_table`은 pk가 있고 force_update도
             update_fields도 없으면 **예외 없이 INSERT로 폴백한다** → 삭제된 문의가
             답변까지 붙어 되살아나고 알림도 나간다. 부모가 부활했으니 FK 위반도
             나지 않아 아무도 모른다(3차 리뷰 — 2차의 "FK 위반으로 드러난다"는
             분석이 틀렸다).

        `request.method != "POST"` 가드가 필수다 — admin의 `changeform_view`는
        GET/HEAD/OPTIONS/TRACE를 **transaction.atomic 밖에서** 처리하므로, 조회에도
        잠그면 `TransactionManagementError`가 난다.

        `in_atomic_block` 가드도 함께 둔다 — `get_object` 호출부 셋 중 `history_view`만
        atomic 밖이라, 그 URL로 POST가 들어오면 method 가드를 통과해 500이 난다.
        도달 확률은 낮지만(UI에 그 경로가 없다) 조건 하나로 닫힌다.

        `of=("self",)`도 필수다 — 위 get_queryset의 `select_related("answer")`가
        역방향 OneToOne이라 LEFT OUTER JOIN을 만드는데, PostgreSQL은 outer join의
        nullable 쪽에 FOR UPDATE를 걸 수 없다. 잠글 대상을 문의 행으로 한정한다.
        """
        if request.method != "POST" or not connection.in_atomic_block:
            return super().get_object(request, object_id, from_field)

        queryset = self.get_queryset(request).select_for_update(of=("self",))
        # get_field는 역참조(ForeignObjectRel)도 반환할 수 있는 유니온이라 to_python이
        # 없을 수 있다. admin의 from_field는 to_field_allowed를 통과한 실제 필드뿐이고
        # 이 admin은 to_field를 쓰지 않으므로 사실상 pk 경로만 탄다.
        field = cast(
            "Field[Any, Any]",
            (
                Inquiry._meta.pk
                if from_field is None
                else Inquiry._meta.get_field(from_field)
            ),
        )
        try:
            return queryset.get(**{field.name: field.to_python(object_id)})
        except (Inquiry.DoesNotExist, ValidationError, ValueError):
            return None

    @admin.display(description="첨부 이미지")
    def image_preview(self, obj: Inquiry) -> Any:
        """버킷이 비공개라 key만 보여주면 운영진도 첨부를 확인할 수 없다.
        조회용 presigned URL(기본 15분)을 링크로 건다.
        """
        if not obj.img_key:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noreferrer">첨부 열기</a>'
            '<div style="color:#5f6368;font-size:11px">{}</div>',
            s3_svc.create_download_presigned_url(obj.img_key),
            obj.img_key,
        )

    @admin.display(description="상태", ordering="status")
    def status_badge(self, obj: Inquiry) -> Any:
        return format_html(
            '<b style="color:{}">{}</b>',
            _STATUS_COLORS.get(obj.status, "#5f6368"),
            obj.get_status_display(),
        )

    # permissions가 없으면 Django는 이 액션을 무조건 통과시킨다
    # (_filter_actions_by_permissions가 allowed_permissions 없는 액션은 필터 없이 넣는다).
    # changelist는 view 권한만으로 열리므로, 이게 없으면 조회 권한만 가진 스태프가
    # 문의 상태를 바꿀 수 있어 has_add_permission=False·readonly로 세운 경계와 어긋난다.
    @admin.action(
        permissions=["change"], description="선택한 문의를 종결 처리 (답변 없이 닫기)"
    )
    def close_inquiries(self, request: HttpRequest, queryset: QuerySet) -> None:
        """스팸·중복처럼 답변할 가치가 없는 문의를 일괄 종결한다.

        답변이 달린 문의는 제외한다 — ANSWERED를 CLOSED로 덮으면 "답변했다"는
        사실이 목록에서 사라져 처리 이력이 흐려진다. queryset.update는 auto_now를
        건너뛰므로 updated_at을 명시한다.
        """
        # 선택 건수를 update **이전에** 센다. update 이후에 세면 queryset이 다시
        # 평가되면서 방금 CLOSED로 바뀐 행이 필터에서 빠져 skipped가 음수가 된다.
        selected = queryset.count()
        target = queryset.filter(answer__isnull=True).exclude(status=InquiryStatus.CLOSED)
        updated = target.update(status=InquiryStatus.CLOSED, updated_at=timezone.now())
        skipped = selected - updated
        message = f"{updated}건을 종결 처리했습니다."
        if skipped:
            message += f" ({skipped}건은 이미 답변·종결된 문의라 제외)"
        self.message_user(request, message)

    def has_add_permission(self, request: HttpRequest) -> bool:
        # 문의는 사용자가 API로만 만든다.
        return False


@admin.register(PendingInquiryAttachmentDeletion)
class PendingInquiryAttachmentDeletionAdmin(admin.ModelAdmin):
    """파기 대장 조회 전용.

    대장은 "적어만 두고 아무도 읽지 않는" 상태였다 — 브로커가 메시지를 잃으면
    (redis OOM·AOF 유실) 로그조차 남지 않아 psql로 직접 조회해야 발견됐다.
    파기 이행을 입증하려면 최소한 볼 수 있어야 한다(5차 리뷰).

    행이 오래 남아 있다면 둘 중 하나다:
      ① 파기가 아직 안 됐다 — 회수 대상
      ② 다른 문의가 같은 key를 참조해 보류됐다(tasks의 "파기 보류" 로그)
    ②는 참조가 사라지면 자동으로 파기되므로 회수 대상이 아니다. 주기 재구동
    (`tasks.redrive_pending_attachment_deletions`)도 같은 기준으로 "대장에 있으면서
    **어떤 Inquiry도 참조하지 않는** key"만 고른다.

    쓰기는 막는다 — 대장은 코드가 관리하는 상태이고, 손으로 지우면 파기되지 않은
    개인정보의 유일한 기록이 사라진다.
    """

    list_display = ("key", "referenced_by_live_inquiry", "created_at")
    ordering = ("created_at",)
    search_fields = ("key",)
    show_full_result_count = False

    def get_queryset(
        self, request: HttpRequest
    ) -> QuerySet[PendingInquiryAttachmentDeletion]:
        # 행마다 exists()를 치면 100행 목록이 101쿼리가 된다 — 1쿼리로 합친다.
        return (
            super()
            .get_queryset(request)
            .annotate(_referenced=Exists(Inquiry.objects.filter(img_key=OuterRef("key"))))
        )

    @admin.display(
        description="살아 있는 문의가 참조 중", boolean=True, ordering="_referenced"
    )
    def referenced_by_live_inquiry(self, obj: PendingInquiryAttachmentDeletion) -> bool:
        return bool(getattr(obj, "_referenced", False))

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: PendingInquiryAttachmentDeletion | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: PendingInquiryAttachmentDeletion | None = None
    ) -> bool:
        return False
