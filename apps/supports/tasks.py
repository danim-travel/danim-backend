"""문의 답변 알림 비동기 발송.

admin에서 답변을 저장하는 순간 알림 생성·캐시 갱신·웹소켓 푸시가 동기로 붙으면
운영진의 저장 화면이 Redis/채널 레이어 응답을 기다린다. 장애 시 답변 저장 자체가
느려지거나 실패하므로 Celery로 분리한다(2단계에서 워커 투입이 선행 조건이었던 이유).
"""

import logging

from celery import shared_task

from apps.notifications.models.model import NotificationType, TargetChoices
from apps.notifications.utils.create_notification import create_noti
from apps.supports.models import Inquiry

logger = logging.getLogger(__name__)

INQUIRY_ANSWERED_MESSAGE = "문의하신 내용에 답변이 등록되었습니다."


@shared_task(bind=True, max_retries=3)
def notify_inquiry_answered_task(self, inquiry_id: str) -> None:
    """문의 답변 등록 알림.

    사용자 간 알림 경로(create_notification)를 쓰지 않고 create_noti를 직접 부른다.
    그 경로에는 이 알림에 맞지 않는 규칙이 세 개 있다:
      - 차단 게이트: 사용자가 운영자 계정을 차단해 두면 답변 알림이 조용히 사라진다.
        문의 답변은 사용자가 먼저 요청한 것이라 사회적 관계로 막을 대상이 아니다.
      - 자기 알림 차단(receiver == sender): sender가 없는 알림이라 성립하지 않는다.
      - NOTIFICATION_MAP: 모든 문구가 sender 닉네임을 포맷에 넣는데, 답변자는 특정
        운영자가 아니라 서비스다. 담당자 닉네임이 사용자에게 노출되어서도 안 된다.

    조건: 문의가 이미 삭제됐으면 재시도해도 결과가 같으므로 경고만 남기고 종료한다.
    예외: 그 밖의 실패는 지수 백오프로 재시도한다.
    """
    try:
        receiver_id = (
            Inquiry.objects.filter(id=inquiry_id)
            .values_list("user_id", flat=True)
            .first()
        )
        if receiver_id is None:
            logger.warning(f"[문의 답변 알림 스킵] 삭제된 문의 inquiry_id={inquiry_id}")
            return
        create_noti(
            sender=None,
            receiver_id=receiver_id,
            noti_type=NotificationType.INQUIRY_ANSWERED,
            target_id=inquiry_id,
            target_type=TargetChoices.INQUIRY,
            msg=INQUIRY_ANSWERED_MESSAGE,
        )
    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)
