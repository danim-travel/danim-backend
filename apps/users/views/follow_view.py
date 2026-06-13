from typing import cast

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.utils.pagination import paginate
from apps.users.models import User
from apps.users.schemas.follow_schema import follower_list_schema
from apps.users.serializers.follow_serializer import FollowerResponseSerializer
from apps.users.services.follow_service import FollowService


class Followers(APIView):

    permission_classes = [IsAuthenticated]
    service = FollowService()

    @follower_list_schema
    def get(self, request: Request, user_id: str) -> Response:

        queryset = self.service.get_follower(
            user_id=user_id,
            request_user=cast(User, request.user),
        )
        return paginate(queryset, request, FollowerResponseSerializer)
