from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.posts.services import create_post
from tests.test_posts.core import PostBaseTest


class TestPostCreateService(PostBaseTest):

    def test_create_post(self):
        """post 작성 서비스 메서드 테스트"""
        create_post(self.data_for_create_view, self.user)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(PostSpot.objects.count(), 3)
        self.assertEqual(Location.objects.count(), 3)
        self.assertEqual(PostSpotImage.objects.count(), 4)
