from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.posts.models import Post


class PostDetailSerializer(serializers.ModelSerializer):
    """게시글 상세 조회 Response Body 직렬화 serializer"""

    post = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    spots = serializers.SerializerMethodField()
    like_count = serializers.IntegerField()
    is_liked = serializers.BooleanField()
    comment_count = serializers.IntegerField()
    is_bookmarked = serializers.BooleanField()
    is_owner = serializers.BooleanField()

    class Meta:
        model = Post
        fields = [
            "post",
            "user",
            "spots",
            "like_count",
            "is_liked",
            "comment_count",
            "is_bookmarked",
            "is_owner",
        ]

    def get_post(self, obj):
        return {
            "post_id": obj.id,
            "title": obj.title,
            "description": obj.description,
            "thumbnail": (
                s3_svc.create_download_presigned_url(obj.thumbnail)
                if obj.thumbnail
                else None
            ),
            "created_at": obj.created_at,
        }

    def get_user(self, obj):
        return {
            "user_id": obj.user.id,
            "nickname": obj.user.nickname,
            "profile_img": obj.user.profile_img_url,
        }

    def get_spots(self, obj):
        return [
            {
                "spot_id": spot.id,
                "location": {
                    "place_name": spot.location.place_name,
                    "address_name": spot.location.address_name,
                    "road_address_name": spot.location.road_address_name,
                    "x": str(spot.location.x),
                    "y": str(spot.location.y),
                },
                "images": [
                    {
                        "img_url": s3_svc.create_download_presigned_url(image.img_key),
                        "original_img": image.original_img,
                        "img_order": image.img_order,
                    }
                    for image in spot.images.all()
                ],
                "content": spot.content,
                "order": spot.order,
            }
            for spot in obj.spots.all()
        ]
