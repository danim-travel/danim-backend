from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.schemas.share_view_schema import post_share_schema
from apps.posts.services.share_service import PostShareService
from apps.users.models import User


class PostShareView(APIView):
    """
    GET api/v1/posts/{post_id}/share
    게시글 공유에 관한 class
    """

    permission_classes = [IsAuthenticated]
    service = PostShareService()

    @post_share_schema
    def get(self, request: Request, post_id: str) -> Response:
        """게시글 공유 view"""
        redirect_url = self.service.get_share_url(
            post_id, cast(User, request.user), request
        )
        return Response({"redirect_url": redirect_url}, status=status.HTTP_200_OK)
