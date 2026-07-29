from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.schemas import post_share_schema
from apps.posts.services.post_service import PostService


class PostShareView(APIView):
    """
    GET api/v1/posts/{post_id}/share
    게시글 공유에 관한 class
    """

    permission_classes = [AllowAny]
    service = PostService()

    @post_share_schema
    def get(self, request: Request, post_id: str) -> Response:
        """게시글 공유 view"""
        redirect_url = self.service.get_share_url(post_id)
        return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)
