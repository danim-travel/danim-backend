from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class BookMark(BaseModel):
    post = models.ForeignKey(
        "posts.Post", related_name="bookmarks", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bookmarks", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "bookmarks"
        indexes = [models.Index(fields=["user", "created_at"])]
        unique_together = (("post", "user"),)
