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
    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=3)
def delete_notification_task(self):
    try:
        with transaction.atomic():

            cutoff = timezone.now() - timedelta(days=30)

            affected_user_ids = list(
                Notification.objects.filter(created_at__lt=cutoff, is_read=False)
                .values_list("receiver_id", flat=True)
                .distinct()
            )

            unread_subquery = (
                Notification.objects.filter(
                    created_at__lt=cutoff, is_read=False, receiver_id=OuterRef("pk")
                )
                .values("receiver_id")
                .annotate(cnt=Count("pk"))
                .values("cnt")
            )

            User.objects.filter(id__in=affected_user_ids).update(
                unread_noti_count=Greatest(
                    F("unread_noti_count")
                    - Coalesce(Subquery(unread_subquery), Value(0)),
                    Value(0),
                )
            )
            Notification.objects.filter(created_at__lt=cutoff).delete()

        if affected_user_ids:
            cache.delete_many([f"user_{uid}_unread_count" for uid in affected_user_ids])

    except Exception as e:
        raise self.retry(exc=e, countdown=2**self.request.retries)
