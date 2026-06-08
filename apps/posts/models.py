from django.conf import settings
from django.db import models

from apps.core.models import BaseModel, TimeStampModel


class Location(BaseModel):
    address_name = models.CharField(max_length=255)
    road_address_name = models.CharField(max_length=255)
    place_name = models.CharField(max_length=255)
    x = models.DecimalField(max_digits=17, decimal_places=14)
    y = models.DecimalField(max_digits=17, decimal_places=14)

    class Meta:
        db_table = "locations"


class Post(TimeStampModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    thumbnail = models.TextField(blank=True, default="")

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
        indexes = [models.Index(fields=["post", "user"])]
        unique_together = (("post", "user"),)
