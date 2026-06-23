from datetime import date

from django.db import transaction
from django.test import TestCase

from apps.posts.models import Location, Post, PostLike, PostSpot, PostSpotImage
from apps.users.models import User
from apps.users.models.models import LoginType


class LocationTest(TestCase):
    """Location 모델 테스트"""

    location: Location

    def setUp(self):
        """Location test를 위한 공통 데이터 생성"""
        self.location = Location.objects.create(
            address_name="제주특별자치도 서귀포시 성산읍 성산리 1",
            road_address_name="제주특별자치도 서귀포시 성산읍 일출로 284-12",
            place_name="성산일출봉",
            x=126.942492,
            y=33.458421,
        )

    def test_create_location(self) -> None:
        """Location 생성 성공 테스트"""
        location = Location.objects.create(
            address_name="제주특별자치도 제주시 건일동 1",
            road_address_name="제주특별자치도 제주시 임항로 111",
            place_name="제주항",
            x=126.521,
            y=33.527,
        )
        self.assertEqual(location.address_name, "제주특별자치도 제주시 건일동 1")
        self.assertEqual(location.road_address_name, "제주특별자치도 제주시 임항로 111")
        self.assertEqual(location.place_name, "제주항")
        self.assertEqual(Location.objects.count(), 2)


class PostTest(TestCase):
    """Post 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )

    def test_create_post(self) -> None:
        """Post 생성 성공 테스트"""
        post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.title, "test_title")
        self.assertEqual(post.description, "test_description")
        self.assertEqual(post.thumbnail, "prod/posts/thumbnail/uuid.jpg")
        self.assertEqual(Post.objects.count(), 1)


class PostSpotTest(TestCase):
    """PostSpot 모델 태스트"""

    def setUp(self):
        self.user = User.objects.create(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.location = Location.objects.create(
            address_name="제주특별자치도 서귀포시 성산읍 성산리 1",
            road_address_name="제주특별자치도 서귀포시 성산읍 일출로 284-12",
            place_name="성산일출봉",
            x=126.942492,
            y=33.458421,
        )

    def test_create_post_spot(self) -> None:
        """PostSpot 생성 성공 테스트"""
        post_spot = PostSpot.objects.create(
            post=self.post,
            location=self.location,
            content="test_content",
            order=1,
        )
        self.assertEqual(post_spot.post, self.post)
        self.assertEqual(post_spot.location, self.location)
        self.assertEqual(post_spot.content, "test_content")
        self.assertEqual(post_spot.order, 1)
        self.assertEqual(PostSpot.objects.count(), 1)


class PostSpotImageTest(TestCase):
    """PostSpotImage 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.location = Location.objects.create(
            address_name="제주특별자치도 서귀포시 성산읍 성산리 1",
            road_address_name="제주특별자치도 서귀포시 성산읍 일출로 284-12",
            place_name="성산일출봉",
            x=126.942492,
            y=33.458421,
        )
        self.post_spot = PostSpot.objects.create(
            post=self.post,
            location=self.location,
            content="test_content",
            order=1,
        )

    def test_create_post_spot_image(self) -> None:
        """PostSpotImage 생성 성공 테스트"""
        post_spot_image = PostSpotImage.objects.create(
            post_spot=self.post_spot,
            img_key="prod/posts/uuid.jpg",
            original_img="제주도 1일차.png",
            img_order=1,
        )
        self.assertEqual(post_spot_image.post_spot, self.post_spot)
        self.assertEqual(post_spot_image.img_key, "prod/posts/uuid.jpg")
        self.assertEqual(post_spot_image.original_img, "제주도 1일차.png")
        self.assertEqual(post_spot_image.img_order, 1)
        self.assertEqual(PostSpotImage.objects.count(), 1)


class PostLikeTest(TestCase):
    """PostLike 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            name="test",
            nickname="test_nickname",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.user_2 = User.objects.create_user(
            email="test2@example.com",
            name="test2",
            nickname="test_nickname2",
            password="Password@123",
            birth_day=date(1992, 6, 6),
            login_type=LoginType.EMAIL,
        )
        self.post = Post.objects.create(
            user=self.user,
            title="test_title",
            description="test_description",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        self.post_like = PostLike.objects.create(
            post=self.post,
            user=self.user_2,
        )

    def test_create_post_like(self) -> None:
        """PostLike 생성 성공 테스트"""
        post_like = PostLike.objects.create(
            post=self.post,
            user=self.user,
        )
        self.assertEqual(post_like.post, self.post)
        self.assertEqual(post_like.user, self.user)
        self.assertEqual(PostLike.objects.count(), 2)

    def test_fail_unique_together_post_like(self) -> None:
        """PostLike unique_together 적용 테스트"""
        with self.assertRaises(Exception):
            with transaction.atomic():
                PostLike.objects.create(
                    post=self.post,
                    user=self.user_2,
                )
        self.post_like.refresh_from_db()
        self.assertEqual(PostLike.objects.count(), 1)

    def test_delete_post_cascades_post_like(self) -> None:
        """Post 삭제 시 PostLike CASCADE 적용 테스트"""
        self.post.delete()
        self.assertEqual(PostLike.objects.count(), 0)
