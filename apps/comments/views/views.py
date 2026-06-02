from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comments.serializers import (
    CommentCreateResponseSerializer,
    CommentCreateSerializer,
)
from apps.comments.services import create_comment


class CommentView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=CommentCreateSerializer,
        responses={
            201: CommentCreateResponseSerializer,
            400: OpenApiResponse(
                description='{"error_detail" : ["content와 comment_img 두 항목 하나는 입력해야 합니다"],"status_code" : 400}\n {"error_detail" : "content는 100자 이하로 작성되어야합니다.","status_code" : 400}',
            ),
            401: OpenApiResponse(
                description='{"error_detail" : "로그인이 필요합니다.","status_code" : 401}'
            ),
            404: OpenApiResponse(
                description='{"error_detail" : "게시글에 대한 정보를 찾지 못했습니다.","status_code" : 404}"}'
            ),
        },
        tags=["comments"],
        summary="댓글 생성",
    )
    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_comment = create_comment(serializer.validated_data, request.user)
        return Response(
            CommentCreateResponseSerializer(new_comment).data,
            status=status.HTTP_201_CREATED,
        )
