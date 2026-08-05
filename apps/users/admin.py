from django.contrib import admin

from apps.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """운영 참고용 조회 + 계정 권한 관리.

    회원 정보는 서비스 API로만 변경한다 — admin에서는 계정 상태/권한
    (is_active, is_staff)만 수정 가능하고 나머지는 전부 읽기 전용.
    생성/삭제 불가(가입은 서비스 플로우, 탈퇴는 본인 API로만).
    """

    list_display = (
        "email",
        "nickname",
        "login_type",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("login_type", "is_active", "is_staff")
    search_fields = ("email", "nickname")
    ordering = ("-created_at",)

    fields = (
        "email",
        "nickname",
        "name",
        "login_type",
        "birth_day",
        "intro",
        "is_email_verified",
        "is_phone_verified",
        "unread_noti_count",
        "created_at",
        "updated_at",
        "is_active",
        "is_staff",
    )
    readonly_fields = (
        "email",
        "nickname",
        "name",
        "login_type",
        "birth_day",
        "intro",
        "is_email_verified",
        "is_phone_verified",
        "unread_noti_count",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
