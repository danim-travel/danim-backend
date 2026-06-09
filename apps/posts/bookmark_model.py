from django.conf import settings
from django.db import models

from apps.core.models import BaseModel
from apps.posts.models import Post


class BookMark(BaseModel):
    post = models.ForeignKey(Post, related_name="bookmarks", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="bookmarks", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "bookmarks"
        unique_together = (("post", "user"),)
