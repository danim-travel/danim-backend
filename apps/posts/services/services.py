from django.db import transaction

from apps.posts.models import Location, Post, PostSpot, PostSpotImage


@transaction.atomic
def create_post(data, user):

    data_for_post = {
        "user": user,
        "title": data.get("title"),
        "description": data.get("description"),
        "thumbnail": data.get("thumbnail"),
    }

    new_post = Post.objects.create(**data_for_post)

    spot_datas = data.get("spots")
    for spot_data in spot_datas:

        location, _ = Location.objects.get_or_create(**spot_data.get("location"))

        data_for_spot = {
            "post": new_post,
            "content": spot_data.get("content"),
            "location": location,
            "order": spot_data.get("order"),
        }
        spot_post = PostSpot.objects.create(**data_for_spot)

        image_datas = spot_data.get("images")

        images = [
            PostSpotImage(
                post_spot=spot_post,
                img_key=img.get("key"),
                original_img=img.get("original_img"),
                img_order=index,
            )
            for index, img in enumerate(image_datas, start=1)
        ]
        PostSpotImage.objects.bulk_create(images)
