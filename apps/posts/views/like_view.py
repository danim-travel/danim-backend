from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.schemas.like_view_schema import post_like_schema, post_unlike_schema
from apps.posts.services.like_service import PostLikeService
from apps.users.models import User


class PostLikeView(APIView):
    """
    POST api/v1/posts/{post_id}/like
    DELETE api/v1/posts/{post_id}/like
    게시글 좋아요 및 좋아요 취소에 관한 class
    """

    permission_classes = [IsAuthenticated]
    service = PostLikeService()

    @post_like_schema
    def post(self, request: Request, post_id: str) -> Response:
        """게시글 좋아요 view"""
        post = self.service.like_post(post_id, cast(User, request.user))
        return Response(
            {"is_liked": True, "like_count": post.like_count},
            status=status.HTTP_201_CREATED,
        )

    @post_unlike_schema
    def delete(self, request: Request, post_id: str) -> Response:
        """게시글 좋아요 취소 view"""
        post = self.service.unlike_post(post_id, cast(User, request.user))
        return Response(
            {"is_liked": False, "like_count": post.like_count},
            status=status.HTTP_200_OK,
        )
