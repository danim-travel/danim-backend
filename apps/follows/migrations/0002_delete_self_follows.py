from django.db import migrations
from django.db.models import F


def delete_self_follows(apps, schema_editor):
    """follower == following 인 self-follow 행 정리 (과거 가드 부재로 생성된 데이터)."""
    Follows = apps.get_model("follows", "Follows")
    Follows.objects.filter(follower=F("following")).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("follows", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(delete_self_follows, migrations.RunPython.noop),
    ]
