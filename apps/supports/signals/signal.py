"""FAQ 캐시 무효화 · 문의 답변 후처리 · 문의 첨부 정리.

- FAQ: 운영진이 admin에서 카테고리/질문을 저장·삭제하면 조회 캐시를 비워
  챗봇에 즉시 반영되게 한다 (TTL 만료를 기다리지 않음).
- 문의: 답변이 처음 등록되면 문의 상태를 ANSWERED로 바꾸고 알림을 예약한다.
- 문의: 삭제되면 첨부 이미지(S3 객체)도 함께 지운다.
"""

import logging
from typing import Any

from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from apps.core.storage.s3 import s3_svc
from apps.supports.models import FAQ, FAQCategory, Inquiry, InquiryAnswer, InquiryStatus
from apps.supports.services import invalidate_faq_cache
from apps.supports.tasks import notify_inquiry_answered_task

logger = logging.getLogger(__name__)


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


def _delete_attachment(key: str) -> None:
    """S3 객체 삭제. 실패는 삼키고 로그로 남긴다.

    사용자의 삭제 요청은 DB 커밋으로 이미 성립했다. 여기서 예외를 올리면 on_commit
    콜백이 터져 응답 이후 경로에서 오류가 나고, 사용자에게는 아무 의미도 없다.
    남은 고아 객체는 로그로 추적한다.
    """
    try:
        s3_svc.delete(key)
    except Exception as e:
        logger.warning(
            f"[문의 첨부 삭제 실패] 고아 객체가 남았습니다 key={key} error={e}"
        )


@receiver(post_delete, sender=Inquiry)
def delete_inquiry_attachment(sender: type, instance: Inquiry, **kwargs: Any) -> None:
    """문의가 지워지면 첨부 이미지도 함께 지운다.

    **이 도메인만 예외적으로 S3를 정리하는 이유**: `delete_my_inquiry`가 목적을
    "잘못 올렸거나 개인정보를 적어 지우고 싶은 경우"로 명시하는데, 첨부 스크린샷에
    같은 정보가 담겨 있으면 행만 지우는 것은 거짓 약속이 된다. 버킷에 수명 주기
    규칙이 없음을 확인했으므로(2026-08-11) 방치하면 영구 잔존한다.
    형제 도메인(게시글·댓글·DM·프로필)도 같은 상태지만 그쪽은 "지운다"를 개인정보
    사유로 약속하지 않아 별도 과제로 둔다.

    post_delete에 거는 이유: 삭제 경로가 셋이다(사용자 API, admin 개별/일괄 삭제,
    사용자 탈퇴 시 CASCADE). 서비스 함수에만 넣으면 나머지 둘이 새어 나간다.

    on_commit 이후에 부르는 이유 둘:
      - 트랜잭션이 롤백되면 문의는 살아 있는데 첨부만 사라진다.
      - S3 호출을 트랜잭션 안에서 하면 네트워크 왕복 내내 행 잠금을 쥔다
        (삭제 경로는 select_for_update로 해당 행을 잠근 상태다).
    """
    key = instance.img_key
    if not key:
        return
    transaction.on_commit(lambda: _delete_attachment(key))
