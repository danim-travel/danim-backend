from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.services.bookmark_service import BookmarkService


class BookmarkView(APIView):
    permission_classes = [IsAuthenticated]
    service = BookmarkService()

    def post(self, request: Request, post_id: str) -> Response:
        self.service.create_bookmark(
            post_id=post_id,
            request_user=request.user,
        )
        return Response({"is_bookmarked": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, post_id: str) -> Response:
        self.service.delete_bookmark(
            post_id=post_id,
            request_user=request.user,
        )
        return Response({"is_bookmarked": False}, status=status.HTTP_200_OK)
