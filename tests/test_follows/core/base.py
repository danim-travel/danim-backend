from rest_framework.test import APIClient

from apps.users.models.models import User
from tests.core.base import BaseUser


class FollowBaseTest(BaseUser):
    client: APIClient
    url_following_user_2: str

    def setUp(self):
        super().setUp()
        self.url_following_user_2 = f"/api/v1/follow/{self.user_2.id}"
