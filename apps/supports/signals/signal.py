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

from apps.supports.models import (
    FAQ,
    FAQCategory,
    Inquiry,
    InquiryAnswer,
    InquiryStatus,
    PendingAttachmentDeletion,
)
from apps.supports.services import invalidate_faq_cache
from apps.supports.tasks import (
    delete_inquiry_attachment_task,
    notify_inquiry_answered_task,
)

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
    robust=True인 이유는 아래 delete_inquiry_attachment 참고 — 브로커 장애가
        커밋 이후 500으로 새어 나가지 않게 한다.
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
    transaction.on_commit(
        lambda: notify_inquiry_answered_task.delay(inquiry_id), robust=True
    )


def _schedule_attachment_deletion(key: str) -> None:
    """파기 태스크를 예약하고, 실패하면 **key를 로그에 남긴다.**

    `robust=True`만으로는 부족하다. Django가 훅 예외를 삼킬 때 찍는 로그는
    `f"Error calling {func.__qualname__} in on_commit() ..."`인데, 람다를 넘기면
    qualname이 `delete_inquiry_attachment.<locals>.<lambda>`라 **key가 클로저 안에
    있어 출력되지 않는다.** 행은 이미 지워져 DB 어디에도 key가 없으므로, 그 로그로는
    "무엇을 지워야 하는지"를 복구할 수 없다(3차 리뷰 HIGH).

    브로커 장애로 예약이 실패해도 사용자 요청(행 삭제)은 이미 커밋됐다. 되돌릴 수
    없으니 예외를 올리지 않고, 대신 key를 ERROR로 남겨 수동 회수가 가능하게 한다.
    """
    try:
        delete_inquiry_attachment_task.delay(key)
    except Exception as exc:
        logger.error(
            "[문의 첨부 파기 예약 실패] 브로커에 전달하지 못했습니다 — 이 key를 "
            f"수동으로 파기해야 합니다. key={key} error={exc}"
        )


@receiver(post_delete, sender=Inquiry)
def delete_inquiry_attachment(sender: type, instance: Inquiry, **kwargs: Any) -> None:
    """문의가 지워지면 첨부 파기를 예약한다.

    **이 도메인만 예외적으로 S3를 정리하는 이유**: `delete_my_inquiry`가 목적을
    "잘못 올렸거나 개인정보를 적어 지우고 싶은 경우"로 명시하는데, 첨부 스크린샷에
    같은 정보가 담겨 있으면 행만 지우는 것은 거짓 약속이 된다. 버킷에 수명 주기
    규칙이 없음을 확인했으므로(2026-08-11) 방치하면 영구 잔존한다.
    형제 도메인(게시글·댓글·DM·프로필)도 같은 상태지만 그쪽은 "지운다"를 개인정보
    사유로 약속하지 않아 별도 과제로 둔다.

    post_delete에 거는 이유: 삭제 경로가 셋이다(사용자 API, admin 개별/일괄 삭제,
    사용자 탈퇴 시 CASCADE). 서비스 함수에만 넣으면 나머지 둘이 새어 나간다.

    on_commit 이후에 **예약만** 하는 이유:
      - 트랜잭션이 롤백되면 문의는 살아 있는데 첨부만 사라진다.
      - on_commit 콜백은 비동기가 아니다(`run_and_clear_commit_hooks`가 같은
        스레드에서 동기 호출). 여기서 S3를 직접 부르면 요청이 그만큼 붙잡히고,
        트랜잭션 밖이라 잠금은 풀렸어도 응답 지연은 그대로다. 실제 파기와 재시도는
        태스크가 맡는다(tasks.delete_inquiry_attachment_task).

    `robust=True`는 이 훅에 한해서는 잉여다 — `_schedule_attachment_deletion`이
    예외를 스스로 삼키므로 훅이 raise하지 않는다. 그럼에도 남겨 두는 이유는,
    나중에 그 함수가 예외를 올리도록 바뀌면 **탈퇴 CASCADE에서 훅 하나의 실패가
    남은 훅 전부를 조용히 버리기** 때문이다(non-robust 훅이 raise하면 Django가
    루프를 중단한다). 삼킴이 사라져도 그 파급은 막힌다.
    """
    key = instance.img_key
    if not key:
        return
    # 대장 기록은 **삭제와 같은 트랜잭션**에서 남긴다. 롤백되면 함께 사라지고,
    # 커밋되면 브로커 메시지가 유실돼도 "지워야 할 key"가 DB에 남는다.
    PendingAttachmentDeletion.objects.get_or_create(key=key)
    transaction.on_commit(lambda: _schedule_attachment_deletion(key), robust=True)
