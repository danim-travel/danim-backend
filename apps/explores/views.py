from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions.exception import ValidationException
from apps.core.utils.base62 import decode_cursor
from apps.explores.schemas import explore_schema
from apps.explores.serializers import ExploreQuerySerializer, ExploreResponseSerializer
from apps.explores.services.feed import get_explore_feed
from apps.explores.services.response_base import build_next
from apps.explores.services.search import feeds_for_search


class ExploresView(APIView):
    permission_classes = [IsAuthenticated]

    @explore_schema
    def get(self, request):
        req = ExploreQuerySerializer(data=request.query_params)
        req.is_valid(raise_exception=True)

        search = req.validated_data["search"]
        raw_cursor = req.validated_data["cursor"]
        page_size = req.validated_data["page_size"]
        seed = req.validated_data["seed"]

        base_url = request.build_absolute_uri(request.path)

        if search:
            results, next_url, seed = self._search(
                search, raw_cursor, page_size, base_url
            )
        else:
            results, next_url, seed = self._feed(
                request.user, raw_cursor, seed, page_size, base_url
            )

        response_data = {"next": next_url, "seed": seed, "results": results}
        res = ExploreResponseSerializer(response_data)
        return Response(res.data, status=status.HTTP_200_OK)

    # ── 검색: 커서(post id) 기반 페이지네이션 ──────────────────────────────
    def _search(self, search, raw_cursor, page_size, base_url):
        cursor = decode_cursor(raw_cursor) if raw_cursor else None
        feeds, new_cursor, seed = feeds_for_search(search, cursor)
        next_url = (
            build_next(base_url, search=search, cursor=new_cursor, page_size=page_size)
            if new_cursor
            else None
        )
        return feeds, next_url, seed

    def _feed(self, viewer, raw_cursor, seed, page_size, base_url):
        page = self._page_from_cursor(raw_cursor)
        results, seed = get_explore_feed(
            viewer=viewer, page=page, seed=seed, limit=page_size
        )

        # seed 를 함께 실어줘야 다음 페이지가 같은 정렬을 이어받음.
        has_next = len(results) == page_size
        next_url = (
            build_next(
                base_url,
                cursor=str(page + 1),
                page_size=page_size,
                seed=seed,
            )
            if has_next
            else None
        )
        return results, next_url, seed

    @staticmethod
    def _page_from_cursor(raw_cursor) -> int:
        """피드 커서는 페이지 번호임. 검색 커서와 달리 base64가 아님."""
        if not raw_cursor:
            return 0
        try:
            page = int(raw_cursor)
        except (TypeError, ValueError):
            raise ValidationException("잘못된 커서값입니다.")
        if page < 0:
            raise ValidationException("잘못된 커서값입니다.")
        return page
