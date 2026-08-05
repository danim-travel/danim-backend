from django.contrib import admin

from apps.posts.models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    """운영 참고용 read-only 조회. 게시글 변경/삭제는 서비스 API로만 한다."""

    list_display = (
        "id",
        "title",
        "user",
        "like_count",
        "comment_count",
        "view_count",
        "created_at",
    )
    search_fields = ("title", "user__nickname")
    ordering = ("-created_at",)
    list_select_related = ("user",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
