from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.near_postspot.schemas import near_user_schema
from apps.posts.near_postspot.serializers import (
    NearUserQuerySerializer,
    NearUserResponseSerializer,
)
from apps.posts.near_postspot.services import get_near_post_queryset


class NearPostSpotUserView(APIView):
    permission_classes = [IsAuthenticated]

    @near_user_schema
    def get(self, request):
        query_serializer = NearUserQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        queryset = get_near_post_queryset(query_serializer.validated_data)
        return Response(
            NearUserResponseSerializer({"top_near": queryset}).data,
            status=status.HTTP_200_OK,
        )
