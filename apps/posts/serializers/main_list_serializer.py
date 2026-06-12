from rest_framework import serializers

from apps.core.storage.s3 import s3_svc
from apps.posts.models import Post


class PostMainListSerializer(serializers.ModelSerializer):
    """게시글 메인 리스트 조회 Response Body 직렬화 serializer"""

    user = serializers.SerializerMethodField()
    post = serializers.SerializerMethodField()
    spots = serializers.SerializerMethodField()
    spot_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    like_count = serializers.IntegerField()
    is_liked = serializers.BooleanField()
    is_bookmarked = serializers.BooleanField()

    class Meta:
        model = Post
        fields = [
            "user",
            "post",
            "spots",
            "spot_count",
            "comment_count",
            "like_count",
            "is_liked",
            "is_bookmarked",
        ]

    def get_user(self, obj):
        return {
            "user_id": obj.user.id,
            "nickname": obj.user.nickname,
            "profile_img": obj.user.profile_img_url,
        }

    def get_post(self, obj):
        return {
            "post_id": obj.id,
            "thumbnail": (
                s3_svc.create_download_presigned_url(obj.thumbnail)
                if obj.thumbnail
                else None
            ),
            "description": obj.description,
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
                "order": spot.order,
            }
            for spot in obj.spots.all()
        ]
