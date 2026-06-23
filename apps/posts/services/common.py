from django.db.models import F

from apps.posts.models import Location, Post, PostSpot, PostSpotImage


def create_spot_with_location_and_images(post: Post, spot_data: dict) -> None:
    location_data = spot_data["location"]
    location = Location.objects.create(
        address_name=location_data["address_name"],
        road_address_name=location_data["road_address_name"],
        place_name=location_data["place_name"],
        x=location_data["x"],
        y=location_data["y"],
    )
    post_spot = PostSpot.objects.create(
        post=post,
        location=location,
        content=spot_data.get("content", ""),
        order=spot_data["order"],
    )
    Post.objects.filter(id=post.id).update(spot_count=F("spot_count") + 1)

    for img_order, image_data in enumerate(spot_data.get("images", []), start=1):
        PostSpotImage.objects.create(
            post_spot=post_spot,
            img_key=image_data["key"],
            original_img=image_data["original_img"],
            img_order=img_order,
        )
