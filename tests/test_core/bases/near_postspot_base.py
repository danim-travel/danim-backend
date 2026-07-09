from datetime import date

from django.test import TestCase

from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.users.models import LoginType, User


class NearPostSpotBase(TestCase):

    @classmethod
    def _create_spot(cls, lat, lon, user, post=None, location=None):
        if post is None:
            post = Post.objects.create(
                user=user,
                title="testtitle",
                description="testdescription",
                thumbnail="prod/posts/thumbnail/uuid.jpg",
            )
        if location is None:
            location = Location.objects.create(
                address_name=f"test_{lat}/{lon}",
                road_address_name=f"test_{lat+lon}",
                place_name=f"test_{lat}and{lon}for user{user.name}",
                x=lon,
                y=lat,
            )
        postspot = PostSpot.objects.create(
            post=post,
            location=location,
            content="test",
            order=PostSpot.objects.filter(post=post).count() + 1,
        )
        postspot_image = PostSpotImage.objects.create(
            post_spot=postspot,
            img_key="test_key",
            original_img="test",
            img_order=PostSpotImage.objects.filter(post_spot=postspot).count() + 1,
        )
        return post, location, postspot, postspot_image

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email="test@example.com",
            password="Password@1",
            nickname="test",
            name="test",
            intro="test_intro",
            profile_img="test_key",
            birth_day=date(1970, 1, 1),
            login_type=LoginType.EMAIL,
            is_active=True,
        )
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@2",
            nickname="test2",
            name="test",
            intro="test_intro",
            profile_img="test_key",
            birth_day=date(1970, 1, 1),
            login_type=LoginType.EMAIL,
            is_active=True,
        )
        cls.post_user1, cls.location_user1, cls.postspot_user1, cls.spotimage_user1 = (
            cls._create_spot(37.343, 127.0, cls.user1)
        )
        cls.post_user2, cls.location_user2, cls.postspot_user2, cls.spotimage_user2 = (
            cls._create_spot(37.333, 127.0, cls.user2)
        )
        cls.url = "/api/v1/posts/nearspots/user"
