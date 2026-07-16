from typing import Any, cast

from rest_framework import serializers

from apps.posts.serializers.post_simple_serializer import PostSimpleSerializer
from apps.users.models import User

# 프로필에 함께 내려보내는 게시글 미리보기 개수 상한.
# 무제한 직렬화 + 장당 presigned URL 발급은 게시글 수천 개 유저의 프로필을
# 응답 폭증·DoS 벡터로 만든다. 총 개수는 posts_count로 전달되고,
# 전체 목록이 필요하면 별도 커서 페이지네이션 엔드포인트로 분리한다(후속).
PROFILE_POSTS_PREVIEW_LIMIT = 12


class ProfileResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.CharField(source="profile_img_url", allow_null=True)
    intro = serializers.CharField(allow_null=True)
    follower = serializers.IntegerField(source="follower_count")
    following = serializers.IntegerField(source="following_count")
    is_following = serializers.BooleanField()
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField()

    def get_posts(self, obj: User) -> list[dict[str, Any]]:
        qs = obj.posts.order_by("-id")[:PROFILE_POSTS_PREVIEW_LIMIT]
        return cast(list[dict[str, Any]], PostSimpleSerializer(qs, many=True).data)
