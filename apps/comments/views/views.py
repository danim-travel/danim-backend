from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.pagination import CommentPagination
from apps.comments.schemas import comment_create_schema, comment_list_schema
from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
    CommentListSerializer,
)
from apps.comments.services import create_comment, get_comment_img_url, get_comment_list


class CommentView(APIView):
    """댓글 생성 및 댓글 목록조회 view class"""

    permission_classes = [IsAuthenticatedOrReadOnly]

    @comment_create_schema
    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_comment = create_comment(serializer.validated_data, request.user)
        return Response(
            CommentCreateResponseSerializer(new_comment).data,
            status=status.HTTP_201_CREATED,
        )

    @comment_list_schema
    def get(self, request):
        queryset = get_comment_list(request.query_params.get("post_id"), request.user)
        paginator = CommentPagination()
        page = paginator.paginate_queryset(queryset, request)
        page = get_comment_img_url(page)
        serializer = CommentListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
