"""FAQ 변경 시 캐시 무효화.

운영진이 admin에서 카테고리/질문을 저장·삭제하면 조회 캐시를 비워
챗봇에 즉시 반영되게 한다 (TTL 만료를 기다리지 않음).
"""

from typing import Any

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.supports.models import FAQ, FAQCategory
from apps.supports.services import invalidate_faq_cache


@receiver(post_save, sender=FAQCategory)
@receiver(post_delete, sender=FAQCategory)
@receiver(post_save, sender=FAQ)
@receiver(post_delete, sender=FAQ)
def invalidate_faq_cache_on_change(sender: type, **kwargs: Any) -> None:
    invalidate_faq_cache()
