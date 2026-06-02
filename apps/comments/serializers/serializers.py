from rest_framework import serializers

from apps.comments.models import Comment


class CommentImageSerializer(serializers.Serializer):
    original_img = serializers.CharField(max_length=100)
    key = serializers.CharField(max_length=255)


class CommentCreateSerializer(serializers.Serializer):
    post_id = serializers.CharField(max_length=26)
    content = serializers.CharField(max_length=100, required=False, allow_null=True)
    comment_img = CommentImageSerializer(required=False, allow_null=True)

    def validate(self, data):
        if not data.get("content") and not data.get("comment_img"):
            raise serializers.ValidationError(
                "content와 comment_img 두 항목 중 하나는 입력해야합니다."
            )
        return data


class CommentCreateResponseSerializer(serializers.ModelSerializer):
    comment_img = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "content",
            "comment_img",
            "post_id",
            "user_id",
            "created_at",
            "updated_at",
        ]

    def get_comment_img(self, obj):
        if obj.img_key:
            return {
                "key": obj.img_key,
                "original_img": obj.original_img,
                "img_url": obj.img_url,
            }
        return {
            "key": None,
            "original_img": None,
            "img_url": None,
        }
