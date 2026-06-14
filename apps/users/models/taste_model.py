from django.conf import settings
from django.db import models

from apps.core.models import TimeStampModel


class UserTaste(TimeStampModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taste"
    )
    codeword_counts = models.JSONField(default=dict)
    codebook_version = models.CharField(max_length=16, default="v1")
    alpha = models.FloatField(default=0.0)
