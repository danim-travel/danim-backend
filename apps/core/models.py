from django.db import models
from apps.core.utils.ulid import generate_ulid

class BaseModel(models.Model):
    id = models.CharField(primary_key=True,max_length = 26,default = generate_ulid,editable = False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["id"]
