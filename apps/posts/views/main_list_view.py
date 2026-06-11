from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.posts.serializers.main_list_serializer import PostMainListSerializer
from apps.posts.services.main_list_service import PostMainListService
from apps.users.models import User


class PostMainListView(APIView):
    """
    GET api/v1/posts/main
    메인 리스트 조회에 관한 class
    """

    permission_classes = [IsAuthenticated]
    service = PostMainListService()

    def get(self, request: Request) -> Response:
        """
        팔로잉 피드 게시글 목록을 조회하는 view
        """
        queryset = self.service.get_main_list(cast(User, request.user))
        return paginate(queryset, request, PostMainListSerializer)
