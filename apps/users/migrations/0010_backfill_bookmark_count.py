from django.db import migrations
from django.db.models import Count


def backfill_bookmark_count(apps, schema_editor):
    User = apps.get_model("users", "User")
    BookMark = apps.get_model("posts", "BookMark")

    counts = BookMark.objects.values("user_id").annotate(c=Count("id"))
    users = [User(id=row["user_id"], bookmark_count=row["c"]) for row in counts]
    User.objects.bulk_update(users, ["bookmark_count"], batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_user_bookmark_count_user_bookmark_count_non_negative"),
        ("posts", "0020_post_thumbnail_height_post_thumbnail_width_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_bookmark_count, migrations.RunPython.noop),
    ]
