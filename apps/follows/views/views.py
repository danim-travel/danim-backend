from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.follows.services import create_follow


class FollowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        result = create_follow(user_id, request.user)
        return Response(result, status=status.HTTP_201_CREATED)
