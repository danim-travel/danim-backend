from datetime import date

from django.test import TestCase
from rest_framework.test import APITestCase

from apps.users.models import LoginType, User


class UserBase(TestCase):
    user1: User
    user2: User
    user3: User
    social_user: User

    @classmethod
    def setUpTestData(cls)->None:
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

        # 프로필 이미지가 None인 유저
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
            login_type=LoginType.KAKAO,
        )

        # 소개글이 None인 유저
        cls.user3 = User.objects.create_user(
            email="test3@example.com",
            password="Password@1",
            nickname="test3",
            name="name",
            birth_day=date(1999, 1, 1),
            login_type=LoginType.GOOGLE,
        )

        cls.social_user = User.objects.create_user(
            email="social@example.com",
            password="Password@1",
            nickname="social",
            name="social",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.KAKAO,
        )


class UserViewBase(APITestCase):
    user1: User
    user2: User
    user3: User

    @classmethod
    def setUpTestData(cls):
        cls.user1 = User.objects.create_user(
            email="owner@example.com",
            password="Password@1",
            nickname="owner_nick",
            name="owner",
            birth_day=date(1990, 1, 1),
            login_type=LoginType.EMAIL,
            profile_img="test_key",
            is_active=True,
        )
        cls.user2 = User.objects.create_user(
            email="test2@example.com",
            password="Password@1",
            nickname="test2",
            name="name",
            intro="test_intro",
            birth_day=date(1999, 1, 1),
            login_type=LoginType.KAKAO,
        )

        cls.user3 = User.objects.create_user(
            email="test3@example.com",
            password="Password@1",
            nickname="test3",
            name="name",
            profile_img="test_key",
            birth_day=date(1999, 1, 1),
            login_type=LoginType.GOOGLE,
        )
