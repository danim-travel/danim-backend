from unittest.mock import patch

from django.core.cache import cache

from apps.notifications.models import Notification
from apps.notifications.utils.create_notification import (
    set_cache_noti_for_dm_all,
    set_cache_noti_for_rd,
)
from tests.test_notifications.core.base import NotificationsBaseTest


class TestSetCacheNotiForRd(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.cache_key = f"user_{self.user_2.id}_unread_count"
        self.noti = Notification.objects.create(**self.data_for_follow_noti)

    def test_decr_negative_resync_from_db(self):
        """캐시가 0인 상태에서 decr 호출 시 음수가 되어 DB 값으로 재동기화"""
        cache.set(self.cache_key, 0)

        set_cache_noti_for_rd(self.user_2)

        self.assertEqual(cache.get(self.cache_key), 1)

    def test_missing_cache_key_fallback_to_db(self):
        """캐시 키가 없을 때 ValueError fallback으로 DB 값 재세팅"""
        cache.delete(self.cache_key)

        set_cache_noti_for_rd(self.user_2)

        self.assertEqual(cache.get(self.cache_key), 1)

    def test_decr_negative_calls_push_channel_noti(self):
        """재동기화 후 push_channel_noti가 호출되는지 검증"""
        cache.set(self.cache_key, 0)

        with patch(
            "apps.notifications.utils.create_notification.push_channel_noti"
        ) as mock_push:
            set_cache_noti_for_rd(self.user_2)
            mock_push.assert_called_once_with(self.user_2.id)


class TestSetCacheNotiForDmAll(NotificationsBaseTest):

    def setUp(self):
        super().setUp()
        self.cache_key = f"user_{self.user_2.id}_unread_count"

    def test_count_zero_no_cache_access(self):
        """count=0 이면 캐시를 건드리지 않음"""
        cache.set(self.cache_key, 5)

        set_cache_noti_for_dm_all(self.user_2, 0)

        self.assertEqual(cache.get(self.cache_key), 5)

    def test_decr_negative_resync_from_db(self):
        """캐시보다 count가 커서 음수가 될 때 DB 값으로 재동기화"""
        Notification.objects.create(**self.data_for_follow_noti)
        cache.set(self.cache_key, 0)

        set_cache_noti_for_dm_all(self.user_2, 3)

        self.assertEqual(cache.get(self.cache_key), 1)

    def test_missing_cache_key_fallback_to_db(self):
        """캐시 키가 없을 때 ValueError fallback으로 DB 값 재세팅"""
        Notification.objects.create(**self.data_for_follow_noti)
        cache.delete(self.cache_key)

        set_cache_noti_for_dm_all(self.user_2, 1)

        self.assertEqual(cache.get(self.cache_key), 1)
