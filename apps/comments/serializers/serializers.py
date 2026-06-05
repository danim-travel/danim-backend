from rest_framework import serializers

from apps.comments.models import Comment
from apps.core.storage.s3 import s3_svc


class CommentImageURLMixin:
    """
    comment_img의 img_url을 s3_svc.create_img_url을 사용해 생성하는 MixIn
    객체에 img_key 필드가 없으면 None으로 반환함
    comment_img 필드를 SerializerMethodField로 설정하고 해당 MixIn을 상속받아서 사용
    필드의 구조는 아래와 같음
    {
        "key" : str,
        "original_img" : str,
        "img_url" : str,
    }
    """

    def get_comment_img(self, obj):
        if obj.img_key:
            return {
                "key": obj.img_key,
                "original_img": obj.original_img,
                "img_url": s3_svc.create_img_url(obj.img_key),
            }
        return {
            "key": None,
            "original_img": None,
            "img_url": None,
        }


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


class CommentCreateResponseSerializer(CommentImageURLMixin, serializers.ModelSerializer):
    """댓글 생성 후 Response Body의 데이터 직렬화 serializer"""

    comment_id = serializers.CharField(max_length=26, source="id")
    comment_img = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "comment_id",
            "content",
            "comment_img",
            "post_id",
            "user_id",
            "created_at",
            "updated_at",
        ]


class CommentListSerializer(CommentImageURLMixin, serializers.ModelSerializer):
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


class CommentListSwaggerSerializer(serializers.Serializer):
    """swagger를 위한 목록 조회 query_parameter용 serializer"""

    page = serializers.IntegerField(default=1)
    page_size = serializers.IntegerField(default=10)
    post_id = serializers.CharField(max_length=26, default="01J5KXQZ3WNMVP8TQHG2RB4CD")


class CommentUpdateSerializer(serializers.Serializer):
    """댓글 수정 Request Body의 데이터 검증 serializer"""

    content = serializers.CharField(max_length=100, required=False, allow_null=True)
    comment_img = CommentImageSerializer(required=False, allow_null=True)


class CommentUpdateResponseSerializer(CommentImageURLMixin, serializers.ModelSerializer):
    """댓글 수정 후 Response Body의 데이터 직렬화 serializer"""

    comment_img = serializers.SerializerMethodField()
    post_id = serializers.CharField(max_length=26)
    user_id = serializers.CharField(max_length=26)

    class Meta:
        model = Comment
        fields = [
            "content",
            "comment_img",
            "post_id",
            "user_id",
            "created_at",
            "updated_at",
        ]
