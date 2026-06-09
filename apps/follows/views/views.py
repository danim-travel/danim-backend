from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class FollowCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        result = create_follow(user_id, request.user)
        return Response(
            FollowResponseSerializer(result).data, status=status.HTTP_201_CREAETE
        )
