from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.users.schemas import user_search_schema
from apps.users.serializers.user_search_serializer import UserSearchResponseSerializer
from apps.users.services.user_search_service import UserSearchService


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]
    service = UserSearchService()

    @user_search_schema
    def get(self, request: Request) -> Response:
        search = request.query_params.get("search", "").strip()
        queryset = self.service.search_users(search=search)
        return paginate(queryset, request, UserSearchResponseSerializer)
