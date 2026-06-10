from apps.core.exceptions.exception import NotFoundException
from apps.follows.models.models import Follows
from apps.follows.services import create_follow
from tests.test_follows.core.base import FollowBaseTest


class TestFollowService(FollowBaseTest):

    def test_create_follow_service(self):
        """일반 유저의 다른 유저 팔로우 시도 service 성공 테스트"""
        result = create_follow(self.user_2.id, self.user_1)
        self.assertEqual(result["follower_count"], 1)
        self.assertEqual(result["is_followed"], True)
        self.assertEqual(Follows.objects.filter(follower_id=self.user_1.id).count(), 1)
        self.assertEqual(Follows.objects.filter(following_id=self.user_2.id).count(), 1)

    def test_non_user_follow_service(self):
        """없는 유저 팔로잉 시도 service 실패 테스트"""
        with self.assertRaises(NotFoundException):
            result = create_follow("없는아이디", self.user_1)
