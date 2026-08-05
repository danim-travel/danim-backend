from datetime import timedelta
from unittest.mock import patch

from django.core.cache import cache
from django.db.models.query import QuerySet
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.models.model import NotificationType, TargetChoices
from apps.notifications.tasks import delete_notification_task
from apps.users.models import User
from tests.test_notifications.core.base import NotificationsBaseTest


class TestDeleteNotificationTask(NotificationsBaseTest):

    def _create_notification(self, *, receiver, sender, is_read, created_days_ago):
        noti = Notification.objects.create(
            sender=sender,
            receiver=receiver,
            target_id=sender.id,
            target_type=TargetChoices.USER,
            notification_type=NotificationType.FOLLOW,
            message="test",
            is_read=is_read,
        )
        # created_at은 auto_now_add라 생성 시각으로 고정되므로,
        # queryset update로 우회해 과거 시각을 강제로 심는다.
        Notification.objects.filter(id=noti.id).update(
            created_at=timezone.now() - timedelta(days=created_days_ago)
        )
        return noti

    def _cache_key(self):
        return f"user_{self.user_2.id}_unread_count"

    def tearDown(self):
        cache.delete(self._cache_key())
        super().tearDown()

    def test_old_unread_deleted_and_count_decremented(self):
        """30일 지난 미읽음만 삭제되고 그 개수만큼만 차감, 최근 미읽음/카운트는 보존, 캐시 무효화"""
        # 오래된 미읽음 2개 (삭제 + 차감 대상)
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=31
        )
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=31
        )
        # 최근 미읽음 3개 (보존 대상) — 시작 count를 삭제 개수보다 크게 만들어
        # Greatest 바닥처리에 가려지지 않고 차감량 정확도를 검증할 수 있게 한다.
        for _ in range(3):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=1,
            )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=5)
        cache.set(self._cache_key(), 5)

        delete_notification_task.apply()

        # 오래된 2개만 삭제, 최근 3개 보존
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 3)
        self.user_2.refresh_from_db()
        # 5 - 2 = 3 (삭제된 오래된 미읽음 2개만 차감)
        self.assertEqual(self.user_2.unread_noti_count, 3)
        self.assertIsNone(cache.get(self._cache_key()))

    def test_old_read_deleted_without_touching_count(self):
        """30일 지난 읽음 알림은 삭제되지만 unread_noti_count는 건드리지 않는다"""
        # 오래된 읽음 2개 (삭제되지만 count엔 영향 없어야 함)
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=True, created_days_ago=31
        )
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=True, created_days_ago=31
        )
        # 최근 미읽음 3개 (count의 근거)
        for _ in range(3):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=1,
            )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=3)

        delete_notification_task.apply()

        # 오래된 읽음 2개 삭제, 최근 미읽음 3개 보존
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 3)
        self.user_2.refresh_from_db()
        # 읽음 알림 삭제는 count에 영향 없음 → 3 유지
        self.assertEqual(self.user_2.unread_noti_count, 3)

    def test_recent_notifications_preserved(self):
        """30일 이내 알림은 삭제되지 않고 count도 그대로"""
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=10
        )
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=29
        )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=2)

        delete_notification_task.apply()

        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 2)
        self.user_2.refresh_from_db()
        self.assertEqual(self.user_2.unread_noti_count, 2)

    def test_mixed_old_and_recent(self):
        """오래된 읽음+미읽음+최근 미읽음 혼재: 오래된 것만 삭제, 오래된 미읽음 수만큼만 차감"""
        # 오래된 미읽음 2개 (삭제 + 차감)
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=31
        )
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=31
        )
        # 오래된 읽음 1개 (삭제되지만 차감 안 함)
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=True, created_days_ago=31
        )
        # 최근 미읽음 2개 (보존)
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=1
        )
        self._create_notification(
            receiver=self.user_2, sender=self.user_1, is_read=False, created_days_ago=1
        )
        # 전체 미읽음 4개 (오래된 2 + 최근 2)
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=4)
        cache.set(self._cache_key(), 4)

        delete_notification_task.apply()

        # 오래된 3개(읽음 1 + 미읽음 2) 삭제, 최근 2개 보존
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 2)
        self.user_2.refresh_from_db()
        # 4 - 2 = 2 (오래된 미읽음 2개만 차감, 읽음은 차감 안 함)
        self.assertEqual(self.user_2.unread_noti_count, 2)
        self.assertIsNone(cache.get(self._cache_key()))

    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_multi_batch_all_deleted_and_cache_invalidated(self):
        """batch보다 많은 알림도 여러 배치로 나눠 전부 삭제되고 캐시가 무효화된다"""
        # 오래된 미읽음 5개 → batch=2 이므로 3배치(2+2+1)로 처리
        for _ in range(5):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=5)
        cache.set(self._cache_key(), 5)

        delete_notification_task.apply()

        # 5개 전부 삭제
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)
        self.user_2.refresh_from_db()
        # 5 - 5 = 0
        self.assertEqual(self.user_2.unread_noti_count, 0)
        # 여러 배치를 거쳐도 캐시가 무효화됨
        self.assertIsNone(cache.get(self._cache_key()))

    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_mid_batch_failure_keeps_committed_batches(self):
        """중간 배치에서 실패해도 앞서 커밋된 배치는 삭제/차감/캐시 무효화가 유지된다"""
        # 오래된 미읽음 5개 → batch=2, 3배치 예정
        for _ in range(5):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=5)
        cache.set(self._cache_key(), 5)

        # patch 전에 원본 delete를 저장해두고, 두 번째 호출만 실패시킨다.
        real_delete = QuerySet.delete
        call_count = {"n": 0}

        def fail_on_second_delete(qs, *args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("두 번째 배치 삭제 실패")
            return real_delete(qs, *args, **kwargs)

        with patch.object(
            QuerySet, "delete", autospec=True, side_effect=fail_on_second_delete
        ):
            # 재시도 소진 후 예외가 전파되므로 예외를 허용
            with self.assertRaises(Exception):
                delete_notification_task.apply(throw=True)

        # 첫 배치(2개)는 커밋됨 → 5개 중 2개 삭제, 3개 남음
        remaining = Notification.objects.filter(receiver=self.user_2).count()
        self.assertEqual(remaining, 3)
        self.user_2.refresh_from_db()
        # 첫 배치 2개만 차감 → 5 - 2 = 3
        self.assertEqual(self.user_2.unread_noti_count, 3)
        # 첫 배치 커밋 직후 캐시가 무효화됨 (배치별 무효화이므로)
        self.assertIsNone(cache.get(self._cache_key()))

    @patch("apps.notifications.tasks.MAX_BATCHES_PER_RUN", 2)
    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_run_stops_at_batch_cap_and_resumes_next_run(self):
        """회당 상한에 도달하면 남은 분량은 다음 스케줄로 넘긴다.

        solo 풀에서는 정리가 도는 동안 신규 알림 태스크가 직렬로 대기하므로,
        한 번 도는 시간을 상한으로 묶는다.
        """
        for _ in range(7):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )
        User.objects.filter(id=self.user_2.id).update(unread_noti_count=7)

        delete_notification_task.apply()

        # 2배치 × 2건 = 4건만 처리되고 3건이 남는다
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 3)

        delete_notification_task.apply()

        # 다음 실행이 남은 분량을 이어서 처리한다
        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)

    @patch("apps.notifications.tasks.MAX_BATCHES_PER_RUN", 2)
    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_cap_reached_logs_warning(self):
        """상한에 걸려 남은 분량이 있으면 경고 로그를 남긴다.

        상한 도입으로 "태스크 완료 = 전부 삭제" 보장이 사라졌으므로, 정상 완료와
        상한 도달이 로그로 구분되어야 운영에서 적체를 알아챌 수 있다.
        """
        for _ in range(7):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )

        with self.assertLogs("apps.notifications.tasks", level="WARNING") as logs:
            delete_notification_task.apply()

        self.assertTrue(any("상한 도달" in line for line in logs.output))

    @patch("apps.notifications.tasks.MAX_BATCHES_PER_RUN", 2)
    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_exact_cap_without_leftover_does_not_warn(self):
        """총량이 정확히 상한×배치면 전부 지워지므로 경고하지 않는다.

        마지막 배치가 남은 분량을 정확히 소진하면 break를 만날 기회 없이 루프가
        끝나므로, 잔여 확인 없이 경고하면 거짓 적체 신호가 된다.
        """
        for _ in range(4):  # 2배치 × 2건 = 정확히 상한
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )

        with self.assertNoLogs("apps.notifications.tasks", level="WARNING"):
            delete_notification_task.apply()

        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)

    @patch("apps.notifications.tasks.MAX_BATCHES_PER_RUN", 10)
    @patch("apps.notifications.tasks.DELETE_BATCH_SIZE", 2)
    def test_completed_run_does_not_log_cap_warning(self):
        """상한에 닿지 않고 끝나면 경고를 남기지 않는다"""
        for _ in range(3):
            self._create_notification(
                receiver=self.user_2,
                sender=self.user_1,
                is_read=False,
                created_days_ago=31,
            )

        with self.assertNoLogs("apps.notifications.tasks", level="WARNING"):
            delete_notification_task.apply()

        self.assertEqual(Notification.objects.filter(receiver=self.user_2).count(), 0)
