from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Block(BaseModel):
    """유저 차단 관계. blocker가 blocked를 차단했다.

    차단의 효과는 양방향이다 — 어느 쪽이 차단했든 팔로우·DM·댓글·알림
    상호작용이 막힌다(services.is_blocked_between 참조).
    related_name은 방향이 헷갈리지 않도록 관계 명사로 짓는다
    (Follows의 related_name 의미 반전 전례 방지).
    """

    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="block_relations_made",
        on_delete=models.CASCADE,
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="block_relations_received",
        on_delete=models.CASCADE,
    )

    class Meta:
        db_table = "blocks"
        unique_together = (("blocker", "blocked"),)
        constraints = [
            # 자기 차단은 앱 레벨 가드 + DB 제약 이중 방어
            # (Follows는 DB 제약이 없어 자기팔로우 오염을 migration으로 청소한 전례)
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="ck_no_self_block",
            )
        ]
