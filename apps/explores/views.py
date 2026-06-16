from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.base62 import decode_cursor
from apps.explores.serializers import (
    ExploreFeedsSerializer,
    ExploreQuerySerializer,
    ExploreResponseSerializer,
)
from apps.explores.services.order import call_posts
from apps.explores.services.search import build_next, feeds_for_search


class ExploresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        req = ExploreQuerySerializer(data=request.query_params)
        req.is_valid(raise_exception=True)
        search = req.validated_data["search"]
        raw_cursor = req.validated_data["cursor"]
        cursor = decode_cursor(raw_cursor) if raw_cursor else None
        if search:
            feeds, new_cursor, seed = feeds_for_search(search, cursor)
            base_url = request.build_absolute_uri(request.path)
            next_url = build_next(search, new_cursor, base_url) if new_cursor else None
            response_data = {"next": next_url, "seed": seed, "results": feeds}
            res = ExploreResponseSerializer(response_data)

            return Response(res.data, status=status.HTTP_200_OK)

        feeds, new_cursor, seed = call_posts(cursor)
        base_url = request.build_absolute_uri(request.path)
        next_url = build_next(search, new_cursor, base_url) if new_cursor else None
        response_data = {"next": next_url, "seed": seed, "results": feeds}
        res = ExploreResponseSerializer(response_data)

        return Response(res.data, status=status.HTTP_200_OK)
