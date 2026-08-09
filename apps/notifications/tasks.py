import logging
from datetime import timedelta
from typing import Literal

from celery import shared_task
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count, F, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, Greatest
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.utils import create_notification
from apps.users.models import User

logger = logging.getLogger(__name__)

DELETE_BATCH_SIZE = 5000

# 워커를 --pool=solo 로 띄우면 태스크가 한 번에 하나씩만 처리된다. 정리 배치가 남은
# 데이터를 다 지울 때까지 돌면 그동안 신규 알림이 전부 뒤에서 대기하므로, 회당 처리량을
# 묶어 한 번 도는 시간을 예측 가능한 범위로 유지한다. 남은 분량은 다음 스케줄이 이어간다.
#
# [알림 정리 상한 도달] 경고가 반복되면 삭제 수요가 회당 상한(10 x 5000 = 5만건/일)을
# 넘은 것이다. 이때는 상한을 올리기 전에 CELERY_BEAT_SCHEDULE 주기를 먼저 올릴 것 —
# 상한을 키우면 한 번 도는 시간이 같이 늘어 알림 대기 시간이 다시 길어진다.
MAX_BATCHES_PER_RUN = 10


@shared_task(bind=True, max_retries=3)
def create_notification_task(
    self,
    receiver_id: str,
    sender_id: str,
    noti_type: Literal["post_like", "comment", "comment_like", "follow", "dm"],
    target_id: str,
):
    try:
        sender = User.objects.get(
            id=sender_id
        )  # TODO:celery 피펙토링때 create_notification 메서드 수정후 쿼리 삭제예정
        create_notification(receiver_id, sender, noti_type, target_id)
    except (User.DoesNotExist, KeyError) as e:
        # 존재하지 않는 sender나 잘못된 noti_type은 재시도해도 성공할 수 없으므로 스킵
        logger.warning(
            f"[알림 스킵] receiver_id={receiver_id}, sender_id={sender_id}, "
            f"noti_type={noti_type}, error={e}"
        )
        return
    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=3)
def delete_notification_task(self):
    try:
        cutoff = timezone.now() - timedelta(days=30)
        batch = DELETE_BATCH_SIZE

        for _ in range(MAX_BATCHES_PER_RUN):
            with transaction.atomic():
                ids = list(
                    Notification.objects.filter(created_at__lt=cutoff).values_list(
                        "pk", flat=True
                    )[:batch]
                )
                if not ids:
                    break

                receiver_ids = list(
                    Notification.objects.filter(pk__in=ids, is_read=False)
                    .values_list("receiver_id", flat=True)
                    .distinct()
                )

                unread_subquery = (
                    Notification.objects.filter(
                        pk__in=ids, is_read=False, receiver_id=OuterRef("pk")
                    )
                    .values("receiver_id")
                    .annotate(cnt=Count("pk"))
                    .values("cnt")
                )

                User.objects.filter(id__in=receiver_ids).update(
                    unread_noti_count=Greatest(
                        F("unread_noti_count")
                        - Coalesce(Subquery(unread_subquery), Value(0)),
                        Value(0),
                    )
                )
                Notification.objects.filter(pk__in=ids).delete()

            try:
                cache.delete_many([f"user_{uid}_unread_count" for uid in receiver_ids])
            except Exception as e:
                logger.warning(
                    f"[캐시 무효화 실패] receiver_ids={len(receiver_ids)}건, error={e}"
                )
        else:
            # break 없이 루프가 끝났다 = 상한을 다 썼다. 상한 도입으로 "태스크 완료 =
            # 전부 삭제" 보장이 사라졌으므로 정상 완료와 적체를 로그로 구분한다.
            # 다만 마지막 배치가 남은 분량을 정확히 소진하면 break를 만날 기회 없이
            # 루프가 끝나므로, 실제로 남았는지 확인한 뒤에만 경고한다.
            # 이 경고가 반복되면 삭제 속도가 생성 속도를 따라가지 못하는 것이므로
            # 상한이나 스케줄 주기를 조정해야 한다.
            if Notification.objects.filter(created_at__lt=cutoff).exists():
                logger.warning(
                    f"[알림 정리 상한 도달] {MAX_BATCHES_PER_RUN}배치"
                    f"({MAX_BATCHES_PER_RUN * batch}건) 처리 후 종료, "
                    f"남은 분량은 다음 스케줄에서 처리됩니다."
                )

    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)
