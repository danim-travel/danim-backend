"""문의 답변 알림 발송 · 첨부 파기 (둘 다 비동기).

외부 I/O를 요청 스레드에 붙이지 않는다는 같은 이유로 둘 다 Celery로 뺀다.
- 답변 알림: 동기로 붙으면 운영진의 저장 화면이 Redis/채널 레이어 응답을 기다린다.
- 첨부 파기: S3 왕복이 더 느리고, 탈퇴 CASCADE·admin 일괄 삭제에서는 문의 수만큼
  직렬로 쌓여 탈퇴 API 자체가 타임아웃될 수 있다.
"""

import logging

from celery import shared_task

from apps.core.storage.s3 import s3_svc
from apps.core.storage.s3.services import CategoryEnum
from apps.core.storage.s3.validators import is_valid_attach_key
from apps.notifications.models import NotificationType, TargetChoices
from apps.notifications.utils.create_notification import create_system_notification
from apps.supports.models import Inquiry, PendingInquiryAttachmentDeletion

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


# 전용 큐로 보낸다. 워커가 --pool=solo(순차 처리·task_time_limit 미지원)라
# 기본 큐에 얹으면 S3가 늘어지는 동안 답변 알림이 전부 대기한다
# (docker-compose.dev.yml의 경고 주석이 정확히 이 경우를 금지한다).
#
# acks_late=True는 **이 태스크에만** 건다. 기본값(False)은 실행 시작 시점에 ack해서,
# 배포 down으로 워커가 죽으면 선점했던 메시지가 재배달 없이 증발한다. 행이 이미
# 지워져 key의 유일한 사본이 이 메시지라 그대로 파기 지시가 사라진다(3차 리뷰 HIGH).
# delete_object는 없는 key에도 204를 주는 멱등 연산이라 재배달이 안전하다.
# ⚠ 전역 설정으로 올리면 안 된다 — create_notification_task는 멱등하지 않아
#   재배달이 중복 알림이 된다.
#
# 재배달 계약(reject_on_worker_lost는 --pool=solo에서 무동작이다 — WorkerLostError는
# prefork 풀이 자식 사망 시 올린다. 풀을 바꿀 때를 대비해 켜 두는 것뿐):
#   - graceful 종료(SIGTERM, stop_grace_period 내) → kombu restore_at_shutdown이
#     미ack 메시지를 즉시 큐로 되돌린다.
#   - SIGKILL(유예 초과·OOM-kill) → visibility_timeout(기본 3600초) 뒤에 재배달된다.
#     **최대 1시간 지연**이며 그동안 대장 행이 회수 대상으로 남아 있는다.
#
# 재시도 간격도 늘렸다. 1·2·4초(총 7초)는 S3 일시 장애를 넘기기에 짧다.
@shared_task(
    bind=True,
    max_retries=5,
    queue="s3_cleanup",
    acks_late=True,
    reject_on_worker_lost=True,
)
def delete_inquiry_attachment_task(self, key: str) -> None:
    """삭제된 문의의 첨부 S3 객체를 파기한다.

    Celery로 빼는 이유: `transaction.on_commit` 콜백은 비동기가 아니다 —
    `run_and_clear_commit_hooks()`가 `Atomic.__exit__`에서 **같은 스레드로 동기
    호출**하므로, 그대로 두면 S3 왕복이 끝날 때까지 요청이 리턴하지 못한다.
    botocore 기본 타임아웃(connect/read 60s, 재시도 4회)에 탈퇴 CASCADE·admin
    일괄 삭제의 건수가 곱해지면 탈퇴 API가 통째로 타임아웃될 수 있다.
    같은 파일의 답변 알림이 이미 같은 이유로 분리돼 있다(1차 리뷰 MEDIUM).

    조건: **다른 문의가 같은 key를 참조하면 지우지 않는다.** 같은 커밋의
        `uq_inquiry_img_key`가 "한 key = 한 문의"를 DB에서 보장하므로 이 분기는
        정상 경로에서 도달하지 않는다. 제약 이전에 쌓인 행과 **중복 배달**
        (acks_late라 재배달이 정상 동작이다)을 위한 심층 방어로 남긴다.
        무조건 지우면 삭제가 막힌 문의(ANSWERED는 409)의 첨부까지 사라져 삭제 불가
        불변식이 우회되므로, 이 검사는 "남아 있으면 보존" 쪽으로 실패한다.
    조건: key 형식을 한 번 더 확인한다. 지금은 쓰기 경로가 serializer 하나뿐이라
        도달 불가지만, 첨부 교체 API나 운영 스크립트가 생기면 버킷의 임의 객체를
        지울 수 있는 자리다.
    예외: S3 실패는 지수 백오프로 재시도하고, 재시도를 소진하면 `logger.error`로
        남긴다 — WARNING은 Sentry LoggingIntegration 기본값(event_level=ERROR)에
        걸리지 않아 컨테이너 stderr 한 줄로 끝난다. 파기 실패는 "삼켜도 되는 실패"가
        아니라 사용자에게 한 약속이 깨진 것이라 알림이 떠야 한다.

        소진 판정을 `self.retry` **호출 전에** 직접 한다. `retry(exc=...)`는 소진 시
        `MaxRetriesExceededError`가 아니라 **원본 예외를 다시 던지므로**
        (celery `app/task.py`: `if exc: raise_with_context(exc)`), 그 예외를 잡는
        구조는 죽은 코드가 되고 로그가 영영 찍히지 않는다(2차 리뷰 MEDIUM).
    """
    if not is_valid_attach_key(key, CategoryEnum.INQUIRY):
        logger.error(f"[문의 첨부 파기 거부] 문의용 key 형식이 아닙니다 key={key}")
        return

    if Inquiry.objects.filter(img_key=key).exists():
        # 대장 행은 **의도적으로 유지한다.** 여기서 지우면 M-①의 창이 다시 열린다
        # (다른 태스크가 그 사이 대장이 빈 것을 보고 S3 왕복을 시작한다).
        # 참조가 사라지면 그때 파기된다 — #341의 회수 대상은 "대장에 있으면서
        # 어떤 Inquiry도 참조하지 않는 key"여야 한다(5차 리뷰).
        logger.info(
            f"[문의 첨부 파기 보류] 다른 문의가 아직 참조합니다 key={key} "
            "— 대장 행은 유지한다(참조가 사라지면 그때 파기)"
        )
        return

    try:
        s3_svc.delete(key)
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            logger.error(
                "[문의 첨부 파기 실패] 재시도를 모두 소진했습니다 — 개인정보가 담긴 "
                f"객체가 버킷에 남아 있을 수 있습니다. key={key} error={exc}"
            )
            raise
        # 10·20·40·80·160초 — S3 일시 장애가 몇 분 이어져도 넘긴다.
        raise self.retry(exc=exc, countdown=10 * 2**self.request.retries)

    # 성공을 남긴다. ①개인정보 파기 시점의 증적이고 ②"워커가 돌며 파기 중"과 "워커는
    # 떴는데 메시지가 한 건도 안 온다(큐 오타·시그널 미연결)"를 구분해 준다.
    logger.info(f"[문의 첨부 파기 완료] key={key}")
    # 대장은 **성공한 뒤에만** 지운다. 남아 있는 행은 곧 "아직 파기되지 않은 개인정보"다.
    # try 밖에 두는 이유: 안에 있으면 DB 일시 장애가 "S3 파기 실패"로 오보되고
    # (이미 지웠는데 "객체가 남아 있을 수 있습니다" ERROR가 나간다) 재시도마다 S3
    # 왕복을 반복한다(5차 리뷰 LOW).
    PendingInquiryAttachmentDeletion.objects.filter(key=key).delete()
