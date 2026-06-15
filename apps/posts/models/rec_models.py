from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.core.models import TimeStampModel
from apps.posts.models import Post


class PostRec(TimeStampModel):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="rec")
    raw_embedding = VectorField(dimensions=1024, null=True, blank=True)
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    codewords = models.JSONField(default=dict, blank=True)
    codebook_version = models.CharField(max_length=16, default="v1", blank=True)


class PostClick(TimeStampModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clicks",
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="clicks")

    class Meta:
        db_table = "post_click"
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]
