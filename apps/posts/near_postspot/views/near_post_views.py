from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.posts.near_postspot.schemas.near_post_schema import near_post_schema
from apps.posts.near_postspot.serializers import (
    NearPostQuerySerializer,
    NearPostResponseSerializer,
)
from apps.posts.near_postspot.services import get_postspot_list, get_spots


class NearPostSpotPostView(APIView):
    permission_classes = [IsAuthenticated]

    @near_post_schema
    def get(self, request):
        query_serializer = NearPostQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        spot_list, post_id = get_spots(query_serializer.validated_data)
        result = get_postspot_list(spot_list, post_id)
        return Response(
            NearPostResponseSerializer(result).data, status=status.HTTP_200_OK
        )
