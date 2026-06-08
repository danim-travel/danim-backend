from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.posts.models import Location, Post, PostLike, PostSpot, PostSpotImage
from apps.users.models.models import LoginType, User


class PostBaseTest(TestCase):
    client: APIClient
    user: User
    user_2: User
    post: Post
    location: Location
    post_spot: PostSpot
    post_like: PostLike
    post_spot_image: PostSpotImage
    data_for_post: dict
    data_for_location: dict
    data_for_post_spot: dict
    data_for_spot_image: dict
    data_for_post_like: dict
    data_for_fail_post_like: dict
    create_url: str
    data_for_create_view: dict
    data_for_image_1: dict
    data_for_image_2: dict
    data_for_image_3: dict
    data_for_location_1: dict
    data_for_location_2: dict
    data_for_spot_1: dict
    data_for_spot_2: dict

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="testnickname",
            password="Password@123",
            phone_number="01012345678",
            birth_day=date(1970, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.user_2 = User.objects.create(
            email="test_2@example.com",
            name="test_2",
            nickname="testnickname_2",
            password="Password@123_2",
            phone_number="01012345672",
            birth_day=date(1972, 1, 1),
            is_email_verified=True,
            is_phone_verified=True,
            is_active=True,
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="testtitle",
            description="testdescription",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.location = Location.objects.create(
            address_name="test_address_name_1",
            road_address_name="test_road_address_name_1",
            place_name="test_place_name_1",
            x="127.02758310323954",
            y="37.49803536728867",
        )
        self.post_spot = PostSpot.objects.create(
            post=self.post, location=self.location, content="제주도 탐방 1일차", order=1
        )
        self.post_like = PostLike.objects.create(
            post=self.post,
            user=self.user_2,
        )
        self.data_for_post = {
            "user": self.user,
            "title": "test_title",
            "description": "test_description",
            "thumbnail": "prod/posts/thumbnail/uuid.jpg",
        }
        self.data_for_location = {
            "address_name": "test_address_name",
            "road_address_name": "test_road_address_name",
            "place_name": "test_place_name",
            "x": "127.02758310323954",
            "y": "37.49803536728867",
        }
        self.data_for_post_spot = {
            "post": self.post,
            "location": self.location,
            "content": "test_content_spot",
            "order": 1,
        }
        self.data_for_spot_image = {
            "post_spot": self.post_spot,
            "img_key": "prod/posts/uuid.jpg",
            "original_img": "제주도1일차.png",
            "img_order": 1,
        }
        self.data_for_post_like = {
            "post": self.post,
            "user": self.user,
        }
        self.data_for_fail_post_like = {
            "post": self.post,
            "user": self.user_2,
        }
        self.create_url = "/api/v1/posts"
        self.data_for_image_1 = {
            "original_img": "test_view_original_img__1.png",
            "key": "prod/posts/uuid__1.jpg",
        }
        self.data_for_image_2 = {
            "original_img": "test_view_original_img__2.png",
            "key": "prod/posts/uuid__2.jpg",
        }
        self.data_for_image_3 = {
            "original_img": "test_view_original_img__3.png",
            "key": "prod/posts/uuid__3.jpg",
        }
        self.data_for_image_4 = {
            "original_img": "test_view_original_img__4.png",
            "key": "prod/posts/uuid__4.png",
        }
        self.data_for_location_1 = {
            "address_name": "test_address_1",
            "road_address_name": "test_road_1",
            "place_name": "test_place_1",
            "x": "125.02758310323954",
            "y": "31.49803536728867",
        }
        self.data_for_location_2 = {
            "address_name": "test_address_name",
            "road_address_name": "test_road_address_name",
            "place_name": "test_place_name",
            "x": "127.02758310323954",
            "y": "37.49803536728867",
        }
        self.data_for_spot_1 = {
            "order": 1,
            "content": "test_content_1",
            "location": self.data_for_location_1,
            "images": [self.data_for_image_1, self.data_for_image_2],
        }
        self.data_for_spot_2 = {
            "order": 2,
            "content": "test_content_2",
            "location": self.data_for_location_2,
            "images": [self.data_for_image_3, self.data_for_image_4],
        }
        self.data_for_create_view = {
            "title": "test_title",
            "description": "test_description",
            "thumbnail": "test_thumbnail",
            "spots": [self.data_for_spot_1, self.data_for_spot_2],
        }
