from django.core.cache import cache

from apps.notifications.utils import reset_cache_noti
from tests.test_notifications.core.base import NotificationsBaseTest


class TestResetCache(NotificationsBaseTest):

    def tearDown(self):
        cache.delete(f"user_{self.user_1.id}_unread_count")
        super().tearDown()

    def test_first_reset_cache(self):
        """redis에 키가 없을떄 캐시 생성 테스트"""
        reset_cache_noti(self.user_1)
        self.assertEqual(cache.get(f"user_{self.user_1.id}_unread_count"), 0)

    def test_reset_cache(self):
        """redis 키가 있을때 캐시 초기화 테스트"""
        cache.set(f"user_{self.user_1.id}_unread_count", 10)
        reset_cache_noti(self.user_1)
        self.assertEqual(cache.get(f"user_{self.user_1.id}_unread_count"), 0)
