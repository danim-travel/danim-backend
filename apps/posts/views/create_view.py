from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.serializers.create_serializer import PostCreateSerializer
from apps.posts.services.create_service import PostCreateService
from apps.users.models import User


class PostCreateView(APIView):
    """
    POST api/v1/posts
    게시글 작성에 관한 class
    """

    permission_classes = [IsAuthenticated]
    service = PostCreateService()

    def post(self, request: Request) -> Response:
        """
        user로 부터 data를 받아 게시글을 생성하는 view
        """
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.service.create_post(serializer.validated_data, cast(User, request.user))
        return Response(
            {"detail": "게시글이 작성되었습니다."},
            status=status.HTTP_201_CREATED,
        )
