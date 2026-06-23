from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.follows.schemas import follow_create_schema, follow_delete_schema
from apps.follows.services import create_follow, delete_follow


class FollowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @follow_create_schema
    def post(self, request, user_id):
        result = create_follow(user_id, request.user)
        return Response(result, status=status.HTTP_201_CREATED)

    @follow_delete_schema
    def delete(self, request, user_id):
        result = delete_follow(user_id, request.user)
        return Response(result, status=status.HTTP_200_OK)
