from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.posts.schemas import bookmark_list_schema
from apps.posts.serializers.bookmark_list_serializer import BookmarkListSerializer
from apps.posts.services.bookmark_list_service import BookmarkListService
from apps.users.models import User


class BookmarkListView(APIView):
    permission_classes = [IsAuthenticated]
    service = BookmarkListService()

    @bookmark_list_schema
    def get(self, request: Request) -> Response:
        queryset = self.service.get_bookmark_list(
            request_user=cast(User, request.user),
        )
        return paginate(queryset, request, BookmarkListSerializer)
