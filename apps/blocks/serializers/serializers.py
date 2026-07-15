from rest_framework import serializers

from apps.blocks.models import Block


class BlockListSerializer(serializers.ModelSerializer):
    """내가 차단한 유저 목록 항목"""

    user_id = serializers.CharField(source="blocked.id")
    nickname = serializers.CharField(source="blocked.nickname")
    profile_img = serializers.CharField(
        source="blocked.profile_img_url", allow_null=True
    )

    class Meta:
        model = Block
        fields = ["user_id", "nickname", "profile_img", "created_at"]
