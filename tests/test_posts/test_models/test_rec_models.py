from datetime import date

from django.test import TestCase

from apps.posts.models import Post, PostClick, PostRec
from apps.users.models import User
from apps.users.models.models import LoginType


class RecTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(
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
        cls.post = Post.objects.create(
            user=cls.user,
            title="testtitle",
            description="testdescription",
            thumbnail="prod/posts/thumbnail/uuid.jpg",
        )
        cls.rec = PostRec.objects.create(post=cls.post)
        cls.click = PostClick.objects.create(user=cls.user, post=cls.post)

    def test_rec(self):
        self.assertEqual(self.rec.raw_embedding, None)
        self.assertEqual(self.rec.embedding, None)
        self.assertEqual(self.rec.codewords, {})
        self.assertEqual(self.rec.codebook_version, "v1")

    def test_click(self):
        self.assertEqual(self.click.user, self.user)
        self.assertEqual(self.click.post, self.post)
