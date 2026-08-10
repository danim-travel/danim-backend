"""문의 답변 알림 비동기 발송.

admin에서 답변을 저장하는 순간 알림 생성·캐시 갱신·웹소켓 푸시가 동기로 붙으면
운영진의 저장 화면이 Redis/채널 레이어 응답을 기다린다. 장애 시 답변 저장 자체가
느려지거나 실패하므로 Celery로 분리한다(2단계에서 워커 투입이 선행 조건이었던 이유).
"""

import logging

from celery import shared_task

from apps.notifications.models import NotificationType, TargetChoices
from apps.notifications.utils.create_notification import create_system_notification
from apps.supports.models import Inquiry

logger = logging.getLogger(__name__)

INQUIRY_ANSWERED_MESSAGE = "문의하신 내용에 답변이 등록되었습니다."


@shared_task(bind=True, max_retries=3)
def notify_inquiry_answered_task(self, inquiry_id: str) -> None:
    """문의 답변 등록 알림.

    발신 주체가 서비스이므로 시스템 알림 경로를 쓴다(근거는
    create_system_notification docstring — 차단 게이트·닉네임 포맷·자기 알림 차단이
    모두 이 알림에 맞지 않는다). 목록 화면의 발신자 표기도 그 모듈의
    SYSTEM_NOTI_TYPES가 함께 책임진다.

    조건: 문의가 이미 삭제됐으면 재시도해도 결과가 같으므로 경고만 남기고 종료한다.
    예외: ValueError(SYSTEM_NOTI_TYPES 미등록)는 프로그래밍 오류라 재시도해도 결과가
        같으므로 그대로 올린다 — catch-all로 3회 재시도하면 게이트를 둔 취지가
        무색해지고 같은 실패만 세 번 쌓인다. 그 밖의 실패만 지수 백오프로 재시도한다.
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
        create_system_notification(
            receiver_id=receiver_id,
            noti_type=NotificationType.INQUIRY_ANSWERED,
            target_id=inquiry_id,
            target_type=TargetChoices.INQUIRY,
            msg=INQUIRY_ANSWERED_MESSAGE,
        )
    except ValueError:
        raise
    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)
