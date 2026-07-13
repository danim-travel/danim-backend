import random

from django.conf import settings
from django.contrib.postgres.indexes import GinIndex, OpClass
from django.db import models
from django.db.models.functions import Upper

from apps.core.models import BaseModel, TimeStampModel


class Location(BaseModel):
    address_name = models.CharField(max_length=255)
    road_address_name = models.CharField(max_length=255)
    place_name = models.CharField(max_length=255)
    x = models.DecimalField(max_digits=17, decimal_places=14)
    y = models.DecimalField(max_digits=17, decimal_places=14)

    class Meta:
        db_table = "locations"
        # Django의 __icontains 는 UPPER(col) LIKE UPPER(%s) 로 컴파일되므로
        # 인덱스도 raw 컬럼이 아니라 Upper(컬럼) 식(expression)에 걸어야 실제로 쓰인다.
        indexes = [
            models.Index(fields=["y", "x"], name="ix_locations_y_x"),
            GinIndex(
                OpClass(Upper("address_name"), name="gin_trgm_ops"),
                name="loc_addr_trgm",
            ),
            GinIndex(
                OpClass(Upper("road_address_name"), name="gin_trgm_ops"),
                name="loc_road_addr_trgm",
            ),
            GinIndex(
                OpClass(Upper("place_name"), name="gin_trgm_ops"),
                name="loc_place_trgm",
            ),
        ]


def _get_random():
    return random.random()


class Post(TimeStampModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    thumbnail = models.TextField(blank=True, default="")
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    spot_count = models.PositiveIntegerField(default=0)
    random_score = models.FloatField(default=_get_random, db_index=True)

    class Meta:
        db_table = "posts"


class PostSpot(TimeStampModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="spots")
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="post_spots"
    )
    content = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField()

    class Meta:
        db_table = "post_spots"
        ordering = ["order"]


class PostSpotImage(TimeStampModel):
    post_spot = models.ForeignKey(
        PostSpot, on_delete=models.CASCADE, related_name="images"
    )
    img_key = models.TextField()
    original_img = models.TextField()
    img_order = models.PositiveIntegerField()

    class Meta:
        db_table = "post_spot_images"
        ordering = ["img_order"]


class PostLike(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="post_likes")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )

    class Meta:
        db_table = "post_likes"
        indexes = [
            models.Index(fields=["post", "user"]),
            models.Index(fields=["user", "created_at"]),
        ]
        unique_together = (("post", "user"),)
