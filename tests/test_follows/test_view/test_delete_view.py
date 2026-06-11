from apps.follows.models import Follows
from tests.test_follows.core.base import FollowBaseTest


class TestFollowDeleteView(FollowBaseTest):

    def setUp(self):
        super().setUp()
        self.follow = Follows.objects.create(follower=self.user_1, following=self.user_2)

    def test_delete_follow(self):
        """로그인한 유저의 다른 유저 팔로우 삭제 시도 view 성공 테스트"""
        self.client.force_authenticate(user=self.user_1)
        response = self.client.delete(self.url_following_user_2)
        self.assertEqual(response.status_code, 200)

    def test_fail_delete_follow(self):
        """비로그인 유저 다른 유저 팔로우 삭제 시고 view 실패 테스트"""
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.url_following_user_2)
        self.assertEqual(response.status_code, 401)

    def test_non_user_delete_follow(self):
        """로그인 한 유저의 팔로우 기록이 없는 유저 팔로우 취소 시도 view 실패 테스트"""
        self.client.force_authenticate(user=self.user_3)
        response = self.client.delete(self.url_following_user_2)
        self.assertEqual(response.status_code, 404)
