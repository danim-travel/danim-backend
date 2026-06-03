from rest_framework import serializers

from apps.comments.models import Comment


class CommentImageSerializer(serializers.Serializer):
    """댓글 생성 Request Body의 comment_img의 구조 serializer"""

    original_img = serializers.CharField(max_length=100)
    key = serializers.CharField(max_length=255)


class CommentCreateSerializer(serializers.Serializer):
    """댓글 생성 Request Body 검증 serializer"""

    post_id = serializers.CharField(max_length=26)
    content = serializers.CharField(max_length=100, required=False, allow_null=True)
    comment_img = CommentImageSerializer(required=False, allow_null=True)

    def validate(self, data):
        """
        댓글 Request Body의 데이터 비지니스 검증 메서드
        content와 comment_img 두 필드둥 하나는 필수로 입력을 해야한다
        """
        if not data.get("content") and not data.get("comment_img"):
            raise serializers.ValidationError(
                "content와 comment_img 두 항목 중 하나는 입력해야합니다."
            )
        return data


class CommentCreateResponseSerializer(serializers.ModelSerializer):
    """댓글 생성 후 Response Body의 데이터 직렬화 serializer"""

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
        """
        댓글 생성 후 Response Body에 담을 comment_img 필드의 구조를 정의하는 메서드
        content만 있는 댓글의 경우에는 key와 original_img가 없기 때문에 img_url도 None으로 응답함
        """
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


class CommentListSerializer(serializers.ModelSerializer):
    """댓글 목록 조회 Response Body의 데이터 직렬화 serializer"""

    user = serializers.SerializerMethodField()
    comment_id = serializers.CharField(max_length=26, source="id")
    content = serializers.CharField(allow_null=True)
    comment_img = serializers.SerializerMethodField()
    is_liked = serializers.BooleanField()
    like_count = serializers.IntegerField()

    class Meta:
        model = Comment
        fields = [
            "comment_id",
            "content",
            "user",
            "comment_img",
            "created_at",
            "updated_at",
            "is_liked",
            "like_count",
        ]

    def get_user(self, obj):
        """댓글 생성 후 참조하는 user의 데이터를 Response Body에 구조를 정의하는 메서드"""
        if obj.user:
            return {
                "id": obj.user.id,
                "nickname": obj.user.nickname,
                "profile_img": obj.user.profile_img,
                "is_deleted": False,
            }
        return {
            "id": None,
            "nickname": "탈퇴한 유저",
            "profile_img": None,
            "is_deleted": True,
        }

    def get_comment_img(self, obj):
        """
        댓글 목록 조회 Response Body의 comment_img의 구조를 정의하는 메서드
        content만 있는 댓글의 경우에는 key와 original_img가 없기 때문에 img_url도 None으로 응답함
        """
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


class CommentListSwaggerSerializer(serializers.Serializer):
    """swagger를 위한 목록 조회 query_parameter용 serializer"""

    page = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=10)
    post_id = serializers.CharField(max_length=26, default="01J5KXQZ3WNMVP8TQHG2RB4CD")
