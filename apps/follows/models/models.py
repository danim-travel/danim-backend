from django.conf import settings
from django.db import models

from apps.core.models import BaseModel


class Follows(BaseModel):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="followers", on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="following", on_delete=models.CASCADE
    )

    class Meta:
        db_table = "follows"
        unique_together = (("follower", "following"),)
