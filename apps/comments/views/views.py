from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.schemas import comment_create_schema
from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
)
from apps.comments.services import create_comment


class CommentView(APIView):
    permission_classes = [IsAuthenticated]

    @comment_create_schema
    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_comment = create_comment(serializer.validated_data, request.user)
        return Response(
            CommentCreateResponseSerializer(new_comment).data,
            status=status.HTTP_201_CREATED,
        )
