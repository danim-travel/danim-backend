from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.blocks.serializers import BlockListSerializer
from apps.blocks.services import block_user, get_block_list, unblock_user
from apps.core.utils.pagination import paginate


class BlockListView(APIView):
    """GET /api/v1/blocks — 내가 차단한 유저 목록 (커서 페이지네이션)"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        queryset = get_block_list(request.user)
        return paginate(queryset, request, BlockListSerializer)


class BlockView(APIView):
    """POST/DELETE /api/v1/blocks/{user_id} — 차단 / 차단 해제"""

    permission_classes = [IsAuthenticated]

    def post(self, request: Request, user_id: str) -> Response:
        block_user(request.user, user_id)
        return Response({"blocked": True}, status=status.HTTP_201_CREATED)

    def delete(self, request: Request, user_id: str) -> Response:
        unblock_user(request.user, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
