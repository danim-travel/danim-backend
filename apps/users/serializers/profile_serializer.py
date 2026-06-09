from rest_framework import serializers
from apps.core.storage import s3
from apps.users.models import User


class ProfileResponseSerializer(serializers.Serializer):
    nickname = serializers.CharField()
    profile_img = serializers.SerializerMethodField()
    intro = serializers.CharField(allow_null=True)
    follower = serializers.IntegerField()
    following = serializers.IntegerField()
    is_following = serializers.BooleanField()
    posts = serializers.SerializerMethodField()
    posts_count = serializers.IntegerField()

    def get_profile_img(self,obj:User)->str|None:
        """프로필 이미지를 가져오는 검증"""
        if not obj.profile_img:
            return None
        return s3.s3_svc.create_img_url(obj.profile_img)









