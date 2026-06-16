from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.schemas.detail_view_schema import post_detail_schema
from apps.posts.schemas.update_view_schema import post_update_schema
from apps.posts.serializers.detail_serializer import PostDetailSerializer
from apps.posts.serializers.update_serializer import PostUpdateSerializer
from apps.posts.services.detail_service import PostDetailService
from apps.posts.services.update_service import PostUpdateService
from apps.users.models import User


class PostDetailView(APIView):
    """
    GET api/v1/posts/{post_id}
    게시글 상세 조회에 관한 class
    """

    permission_classes = [IsAuthenticated]
    service = PostDetailService()
    update_service = PostUpdateService()

    @post_detail_schema
    def get(self, request: Request, post_id: str) -> Response:
        """
        post_id에 해당하는 게시글 상세 정보를 조회하는 view
        """
        post = self.service.get_post_detail(post_id, cast(User, request.user))
        return Response(PostDetailSerializer(post).data, status=status.HTTP_200_OK)

    @post_update_schema
    def patch(self, request: Request, post_id: str) -> Response:
        serializer = PostUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.update_service.update_post(
            post_id, serializer.validated_data, cast(User, request.user)
        )
        return Response({"detail": "게시글이 수정되었습니다."}, status=status.HTTP_200_OK)
