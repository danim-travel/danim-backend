from django.core.cache import cache

from apps.notifications.models import Notification
from apps.notifications.utils import set_cache_noti_for_rd
from tests.test_notifications.core.base import NotificationsBaseTest


class TestSetCacheNotiForRd(NotificationsBaseTest):

    def tearDown(self):
        cache.delete(f"user_{self.user_1.id}_unread_count")
        cache.delete(f"user_{self.user_2.id}_unread_count")
        super().tearDown()

    def test_first_set_cache_noti_for_rd(self):
        """알림객체가 존재하지 않고 redis에 해당 키가 없을떄 키 생성 테스트"""
        set_cache_noti_for_rd(self.user_1)
        unread_count = cache.get(f"user_{self.user_1.id}_unread_count")
        self.assertEqual(unread_count, 0)

    def test_first_with_one_noti_set_cache_for_rd(self):
        """알림 객체가 1개 존재하고 redis에 해당 키가 없을 떄 키 생성 테스트"""
        Notification.objects.create(**self.data_for_follow_noti)
        set_cache_noti_for_rd(self.user_2)
        unread_count = cache.get(f"user_{self.user_2.id}_unread_count")
        self.assertEqual(unread_count, 1)

    def test_second_set_cache_noti_for_rd(self):
        """redis에 해당 키가 있을때 키값 갱신 테스트"""
        cache.set(f"user_{self.user_1.id}_unread_count", 1)
        set_cache_noti_for_rd(self.user_1)
        unread_count = cache.get(f"user_{self.user_1.id}_unread_count")
        self.assertEqual(unread_count, 0)
