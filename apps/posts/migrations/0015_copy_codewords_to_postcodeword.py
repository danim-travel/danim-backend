from django.db import migrations


def copy_forward(apps, schema_editor):
    PostEmbedding = apps.get_model("posts", "PostEmbedding")
    PostCodeword = apps.get_model("posts", "PostCodeword")

    rows = [
        PostCodeword(
            embedding=emb,
            codewords=emb.codewords,
            codebook_version=emb.codebook_version,
        )
        for emb in PostEmbedding.objects.all()
    ]
    if rows:
        PostCodeword.objects.bulk_create(rows)


def copy_backward(apps, schema_editor):
    PostCodeword = apps.get_model("posts", "PostCodeword")
    PostCodeword.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("posts", "0014_remove_postembedding_raw_embedding_postcodeword"),
    ]

    operations = [
        migrations.RunPython(copy_forward, copy_backward),
    ]
