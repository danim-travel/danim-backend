from typing import Any

from apps.posts.models import Location, Post, PostSpot, PostSpotImage
from apps.users.models import User


class PostCreateService:

    def create_post(self, data: dict[str, Any], user: User) -> Post:
        """게시글 생성 서비스 로직"""

        post = Post.objects.create(
            user=user,
            title=data["title"],
            description=data.get("description", ""),
            thumbnail=data.get("thumbnail", ""),
        )

        for spot_data in data.get("spots", []):
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
            for img_order, image_data in enumerate(spot_data.get("images", []), start=1):
                PostSpotImage.objects.create(
                    post_spot=post_spot,
                    img_key=image_data["key"],
                    original_img=image_data["original_img"],
                    img_order=img_order,
                )

        return post
