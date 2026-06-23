from django.conf import settings
from django.db import models
from pgvector.django import VectorField

from apps.core.models import TimeStampModel
from apps.posts.models import Post


class PostEmbedding(TimeStampModel):
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="rec")
    embedding = VectorField(dimensions=1024, null=True, blank=True)


class PostCodeword(TimeStampModel):
    embedding = models.ForeignKey(
        PostEmbedding, on_delete=models.CASCADE, related_name="clusters"
    )
    codewords = models.JSONField(default=dict, blank=True)
    codebook_version = models.CharField(max_length=16)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["embedding", "codebook_version"], name="uniq_embedding_version"
            )
        ]


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
