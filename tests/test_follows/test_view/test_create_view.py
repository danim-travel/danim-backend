from apps.follows.models.models import Follows
from tests.test_follows.core.base import FollowBaseTest


class TestFollowCreateView(FollowBaseTest):

    def test_follow_create_view(self):
        """로그인 한 유저저가 다른 유저를 팔로우하는 요청 시도 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_2)
        response = self.client.post(self.create_url_following_user_1)
        self.assertEqual(Follows.objects.count(), 1)
        self.assertEqual(response.data["is_followed"], True)
        self.assertEqual(response.data["follower_count"], 1)
        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_follow_create_view(self):
        """비로그인 유저의 팔로우 시도 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.post(self.create_url_following_user_1)
        self.assertEqual(response.status_code, 401)
