from django.db import IntegrityError

from apps.follows.models.models import Follows
from tests.test_follows.core.base import FollowBaseTest


class TestFollowModel(FollowBaseTest):

    def test_create_follow(self):
        """팔로우 생성 성공 이후 unique_together 적용 여부 테스트"""
        Follows.objects.create(
            follower=self.user_1,
            following=self.user_2,
        )
        self.assertEqual(Follows.objects.count(), 1)
        Follows.objects.create(
            follower=self.user_2,
            following=self.user_1,
        )
        self.assertEqual(Follows.objects.count(), 2)
        with self.assertRaises(IntegrityError):
            Follows.objects.create(
                follower=self.user_1,
                following=self.user_2,
            )
