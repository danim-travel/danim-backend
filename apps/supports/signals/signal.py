"""FAQ 캐시 무효화 · 문의 답변 후처리.

- FAQ: 운영진이 admin에서 카테고리/질문을 저장·삭제하면 조회 캐시를 비워
  챗봇에 즉시 반영되게 한다 (TTL 만료를 기다리지 않음).
- 문의: 답변이 처음 등록되면 문의 상태를 ANSWERED로 바꾸고 알림을 예약한다.
"""

from typing import Any

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.supports.models import FAQ, FAQCategory, Inquiry, InquiryAnswer, InquiryStatus
from apps.supports.services import invalidate_faq_cache
from apps.supports.tasks import notify_inquiry_answered_task


@receiver(post_save, sender=FAQCategory)
@receiver(post_delete, sender=FAQCategory)
@receiver(post_save, sender=FAQ)
@receiver(post_delete, sender=FAQ)
def invalidate_faq_cache_on_change(sender: type, **kwargs: Any) -> None:
    invalidate_faq_cache()


@receiver(post_save, sender=InquiryAnswer)
def mark_answered_and_notify(
    sender: type, instance: InquiryAnswer, created: bool, **kwargs: Any
) -> None:
    """답변 최초 등록 시에만 상태 전이 + 알림.

    조건: created=True일 때만 동작한다. 답변 수정(오탈자 정정 등)마다 알림이 다시
        가면 사용자에게 소음이 되고, 운영자가 CLOSED로 정리한 문의가 PENDING 쪽으로
        되돌아가는 문제도 생긴다.
    알림은 반드시 on_commit 이후에 예약한다 — 트랜잭션이 커밋되기 전에 태스크가
        워커에 도착하면 워커가 아직 없는 행을 조회해 알림이 유실된다.
    """
    if not created:
        return

    inquiry_id = instance.inquiry_id
    # signal 안에서 instance.inquiry.save()를 부르면 Inquiry의 post_save까지 태워
    # 의도치 않은 연쇄가 생긴다. 상태 컬럼만 직접 갱신한다(updated_at은 auto_now라
    # queryset.update로는 갱신되지 않으므로 함께 지정한다).
    Inquiry.objects.filter(id=inquiry_id).update(
        status=InquiryStatus.ANSWERED, updated_at=timezone.now()
    )
    transaction.on_commit(lambda: notify_inquiry_answered_task.delay(inquiry_id))
