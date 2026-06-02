from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Location(BaseModel):
    address_name = models.CharField(max_length=255)
    road_address_name = models.CharField(max_length=255)
    place_name = models.CharField(max_length=255)
    kakao_id = models.BigIntegerField()
    x = models.DecimalField(max_digits=17, decimal_places=14)
    y = models.DecimalField(max_digits=17, decimal_places=14)

    class Meta:
        db_table = "locations"


class Post(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts"
    )
    title = models.CharField(max_length=100)
    content = models.TextField(blank=True, default="")
    thumbnail = models.TextField(blank=True, default="")

    class Meta:
        db_table = "posts"


class PostSpot(BaseModel):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="spots")
    location = models.ForeignKey(
        Location, on_delete=models.PROTECT, related_name="post_spots"
    )
    content = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField()

    class Meta:
        db_table = "post_spots"
        ordering = ["order"]


class PostSpotImage(BaseModel):
    post_spot = models.ForeignKey(
        PostSpot, on_delete=models.CASCADE, related_name="images"
    )
    img_url = models.TextField()
    original_image_url = models.TextField()
    img_order = models.PositiveIntegerField()

    class Meta:
        db_table = "post_spot_images"
        ordering = ["img_order"]
