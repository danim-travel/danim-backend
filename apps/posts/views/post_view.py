from typing import cast

from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.posts.schemas import (
    post_create_schema,
    post_delete_schema,
    post_detail_schema,
    post_main_list_schema,
    post_update_schema,
)
from apps.posts.serializers.create_serializer import PostCreateSerializer
from apps.posts.serializers.detail_serializer import PostDetailSerializer
from apps.posts.serializers.main_list_serializer import PostMainListSerializer
from apps.posts.serializers.update_serializer import PostUpdateSerializer
from apps.posts.services.post_service import PostService
from apps.users.models import User


class PostListCreateView(APIView):
    """
    POST, GET api/v1/posts
    게시글 작성 및 목록 조회 담당 View
    """

    permission_classes = [IsAuthenticated]
    service = PostService()

    @post_create_schema
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

    @post_main_list_schema
    def get(self, request: Request) -> Response:
        """
        팔로잉 피드 게시글 목록을 조회하는 view
        """
        queryset = self.service.get_list(cast(User, request.user))
        return paginate(queryset, request, PostMainListSerializer)


class PostDetailView(APIView):
    """
    GET api/v1/posts/{post_id}
    게시글 상세 조회에 관한 class
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    service = PostService()

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
        self.service.update_post(
            post_id, serializer.validated_data, cast(User, request.user)
        )
        return Response({"detail": "게시글이 수정되었습니다."}, status=status.HTTP_200_OK)

    @post_delete_schema
    def delete(self, request: Request, post_id: str) -> Response:
        self.service.delete_post(post_id, cast(User, request.user))
        return Response({"detail": "게시글이 삭제되었습니다."}, status=status.HTTP_200_OK)
