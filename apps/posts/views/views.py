from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.serializers import PostCreateRequestSerializer


class PostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PostCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        create_post(serializer.validated_data, request.user)
        return Response(
            {"detail": "게시글이 생성되었습니다."}, status=status.HTTP_201_CREATED
        )
