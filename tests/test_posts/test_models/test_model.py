from django.db import transaction

from apps.posts.models import Location, Post, PostLike, PostSpot, PostSpotImage
from tests.test_posts.core import PostBaseTest


class TestPost(PostBaseTest):

    def test_create_post(self):
        """게시글 생성 성공 models 테스트"""
        new_post = Post.objects.create(**self.data_for_post)
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(new_post.user, self.user)
        self.assertEqual(new_post.title, self.data_for_post["title"])
        self.assertEqual(new_post.description, self.data_for_post["description"])
        self.assertEqual(new_post.thumbnail, self.data_for_post["thumbnail"])

    def test_create_location(self):
        """위치 생성 성공 models 테스트"""
        new_location = Location.objects.create(**self.data_for_location)
        self.assertEqual(Location.objects.count(), 2)
        self.assertEqual(
            new_location.address_name, self.data_for_location["address_name"]
        )
        self.assertEqual(
            new_location.road_address_name, self.data_for_location["road_address_name"]
        )
        self.assertEqual(new_location.place_name, self.data_for_location["place_name"])
        self.assertEqual(new_location.x, self.data_for_location["x"])
        self.assertEqual(new_location.y, self.data_for_location["y"])

    def test_create_post_spot(self):
        """핀 생성 성공 models 테스트"""
        new_post_spot = PostSpot.objects.create(**self.data_for_post_spot)
        self.assertEqual(PostSpot.objects.count(), 2)
        self.assertEqual(new_post_spot.location, self.location)
        self.assertEqual(new_post_spot.post, self.post)
        self.assertEqual(new_post_spot.content, self.data_for_post_spot["content"])
        self.assertEqual(new_post_spot.order, self.data_for_post_spot["order"])

    def test_create_post_spot_image(self):
        """핀 이미지 생성 성공 models 테스트"""
        new_post_spot_image = PostSpotImage.objects.create(**self.data_for_spot_image)
        self.assertEqual(PostSpotImage.objects.count(), 1)
        self.assertEqual(new_post_spot_image.post_spot, self.post_spot)
        self.assertEqual(new_post_spot_image.img_key, self.data_for_spot_image["img_key"])
        self.assertEqual(
            new_post_spot_image.original_img, self.data_for_spot_image["original_img"]
        )
        self.assertEqual(
            new_post_spot_image.img_order, self.data_for_spot_image["img_order"]
        )

    def test_create_post_like(self):
        """게시글 좋아요 생성 models 테스트"""
        new_post_like = PostLike.objects.create(**self.data_for_post_like)
        self.assertEqual(PostLike.objects.count(), 2)
        self.assertEqual(new_post_like.user, self.user)
        self.assertEqual(new_post_like.post, self.post)

    def test_fail_unique_together_post_like(self):
        """게시글 생성 시 좋아요 unique together 적용 여부 확인 테스트"""
        with self.assertRaises(Exception):
            with transaction.atomic():
                PostLike.objects.create(**self.data_for_fail_post_like)
        self.post_like.refresh_from_db()
        self.assertEqual(PostLike.objects.count(), 1)

    def test_delete_together_with_post_and_like(self):
        """postlike에서 post CASCADE 적용 테스트"""
        self.post.delete()
        self.assertEqual(PostLike.objects.count(), 0)
