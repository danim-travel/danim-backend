from mypy.nodes import set_flags

from apps.core.exceptions.exception import NotFoundException
from apps.follows.models import Follows
from apps.follows.services import delete_follow
from tests.test_follows.core.base import FollowBaseTest


class TestFollowDeleteService(FollowBaseTest):

    def setUp(self):
        super().setUp()
        self.follow = Follows.objects.create(follower=self.user_1, following=self.user_2)

    def test_follow_delete_service(self):
        """유저 팔로우 취소 요청 service 성공 테스트"""
        result = delete_follow(self.user_2.id, self.user_1)
        self.assertEqual(result["is_followed"], False)
        self.assertEqual(result["follower_count"], 0)
        self.assertEqual(Follows.objects.filter(following=self.user_1).count(), 0)

    def test_fail_follow_delete_service(self):
        """유저 기록이 없는 팔로우 취소 요청 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            delete_follow(self.user_3.id, self.user_2)
