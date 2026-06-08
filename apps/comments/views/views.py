from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.schemas import (
    comment_create_schema,
    comment_delete_schema,
    comment_list_schema,
    comment_update_schema,
)
from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
    CommentListSerializer,
    CommentUpdateResponseSerializer,
)
from apps.comments.serializers.serializers import CommentUpdateSerializer
from apps.comments.services import (
    create_comment,
    delete_comment,
    get_comment_list,
    update_comment,
)
from apps.core.utils.pagination import paginate


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
        return paginate(queryset, request, CommentListSerializer)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @comment_update_schema
    def patch(self, request, comment_id):
        serializer = CommentUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mod_comment = update_comment(serializer.validated_data, request.user, comment_id)
        return Response(
            CommentUpdateResponseSerializer(mod_comment).data,
            status=status.HTTP_200_OK,
        )

    @comment_delete_schema
    def delete(self, request, comment_id):
        delete_comment(comment_id, request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
