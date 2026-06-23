from datetime import date

from django.test import TestCase

from apps.users.models import User, UserTaste
from apps.users.models.models import LoginType


class UserTasteTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
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
        cls.taste = UserTaste.objects.create(user=user)

    def test_user_taste_model(self):
        self.assertEqual(self.taste.codeword_counts, {})
        self.assertEqual(self.taste.codebook_version, "v1")
        self.assertEqual(self.taste.alpha, 0.0)
