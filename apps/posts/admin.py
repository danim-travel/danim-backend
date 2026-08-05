from django.contrib import admin
from django.http import HttpRequest

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
    # ULID PK는 사전순=시간순이라 -id가 -created_at과 동일하면서 PK 인덱스를 탄다
    ordering = ("-id",)
    show_full_result_count = False
    list_select_related = ("user",)

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(
        self, request: HttpRequest, obj: Post | None = None
    ) -> bool:
        return False

    def has_delete_permission(
        self, request: HttpRequest, obj: Post | None = None
    ) -> bool:
        return False
