from django.db import models
from apps.users.models import User,LoginType
from apps.core.models import BaseModel





class SocialAccount(BaseModel):
    social_id = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    login_type = models.CharField(
        max_length=10, choices=LoginType.choices
    )
    class Meta:
        db_table = "social_accounts"
        constraints = [
            models.UniqueConstraint(fields=["login_type","social_id"],name="unique_social_account")

        ]