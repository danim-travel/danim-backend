import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.core.utils.ulid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Block",
            fields=[
                (
                    "id",
                    models.CharField(
                        default=apps.core.utils.ulid.generate_ulid,
                        editable=False,
                        max_length=26,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "blocker",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="block_relations_made",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "blocked",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="block_relations_received",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "blocks",
                "unique_together": {("blocker", "blocked")},
            },
        ),
        migrations.AddConstraint(
            model_name="block",
            constraint=models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")),
                name="ck_no_self_block",
            ),
        ),
    ]
