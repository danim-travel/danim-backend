from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from apps.posts.services.bookmark_list_service import BookmarkListService
from apps.posts.serializers.bookmark_list_serializer import BookmarkListSerializer
from apps.core.utils.pagination import  paginate
from apps.users.models import User
from typing import cast


class BookmarkListView(APIView):
    permission_classes = [IsAuthenticated]
    service = BookmarkListService()

    def get(self,request:Request)->Response:
        queryset = self.service.get_bookmark_list(
            request_user=cast(User, request.user),
        )
        return paginate(queryset, request, BookmarkListSerializer)




